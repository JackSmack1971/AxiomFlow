import asyncio
import json
from typing import Dict, List
from unittest.mock import AsyncMock

import pytest

from axiomflow.runtime.router import (AgentRouter, NoAgentsAvailableError,
                                      PolicyViolationError)

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def agents() -> List[dict]:
    return [
        {
            "id": "agent_python",
            "skills": {"python"},
            "load": 0.2,
            "policies": set(),
            "status": "available",
        },
        {
            "id": "agent_ml",
            "skills": {"ml"},
            "load": 0.3,
            "policies": set(),
            "status": "available",
        },
        {
            "id": "agent_restricted",
            "skills": {"ml"},
            "load": 0.5,
            "policies": {"restricted"},
            "status": "available",
        },
    ]


async def test_route_task_selects_best_agent(agents):
    ml_model = AsyncMock()
    ml_model.score.side_effect = [0.6, 0.9]
    router = AgentRouter(ml_model)
    task = {"required_skill": "python", "complexity": 0.5}
    selected = await router.route_task(task, agents)
    assert selected["id"] == "agent_python"


async def test_no_available_agents(agents):
    ml_model = AsyncMock()
    router = AgentRouter(ml_model)
    task = {"required_skill": "go"}
    with pytest.raises(NoAgentsAvailableError):
        await router.route_task(task, agents)


async def test_policy_violation(agents):
    ml_model = AsyncMock()
    router = AgentRouter(ml_model)
    task = {"required_skill": "ml", "disallowed_policies": {"restricted"}}
    with pytest.raises(PolicyViolationError):
        await router.route_task(task, agents)


async def test_overloaded_agents():
    ml_model = AsyncMock()
    router = AgentRouter(ml_model)
    overloaded = [
        {
            "id": "agent_a",
            "skills": {"python"},
            "load": 0.95,
            "policies": set(),
            "status": "available",
        },
    ]
    task = {"required_skill": "python"}
    with pytest.raises(NoAgentsAvailableError):
        await router.route_task(task, overloaded)


async def test_ml_model_unavailable(agents):
    ml_model = AsyncMock()
    ml_model.score.side_effect = RuntimeError("model down")
    router = AgentRouter(ml_model)
    task = {"required_skill": "python"}
    selected = await router.route_task(task, agents)
    assert selected["id"] == "agent_python"


async def test_routing_accuracy(agents):
    ml_model = AsyncMock()

    async def score(features):
        expected = (
            "agent_python"
            if features["task"]["required_skill"] == "python"
            else "agent_ml"
        )
        return 1.0 if features["agent_id"] == expected else 0.0

    ml_model.score.side_effect = score
    router = AgentRouter(ml_model)
    tasks = [{"required_skill": "python"}] * 10 + [{"required_skill": "ml"}] * 10
    correct = 0
    for t in tasks:
        result = await router.route_task(t, agents)
        if t["required_skill"] == "python" and result["id"] == "agent_python":
            correct += 1
        elif t["required_skill"] == "ml" and result["id"] == "agent_ml":
            correct += 1
    assert correct / len(tasks) >= 0.95


async def test_model_adapts_after_feedback(tmp_path):
    class SimpleModel:
        def __init__(self) -> None:
            self.stats: Dict[str, Dict[str, int]] = {}

        async def score(self, features):
            stat = self.stats.get(features["agent_id"], {"success": 0, "total": 0})
            return (stat["success"] + 1) / (stat["total"] + 2)

        async def update(self, features):
            stat = self.stats.setdefault(
                features["agent_id"], {"success": 0, "total": 0}
            )
            stat["total"] += 1
            if features["result"]:
                stat["success"] += 1

    agents = [
        {
            "id": "agent_a",
            "skills": {"python"},
            "load": 0.2,
            "policies": set(),
            "status": "available",
        },
        {
            "id": "agent_b",
            "skills": {"python"},
            "load": 0.2,
            "policies": set(),
            "status": "available",
        },
    ]
    metrics_file = tmp_path / "metrics.json"
    router = AgentRouter(SimpleModel(), metrics_path=metrics_file)
    task = {"required_skill": "python"}
    first = await router.route_task(task, agents)
    await router.record_outcome(task, first, False)
    second = await router.route_task(task, agents)
    await router.record_outcome(task, second, True)
    third = await router.route_task(task, agents)
    assert second["id"] != first["id"]
    assert third["id"] == second["id"]
    data = json.loads(metrics_file.read_text())
    assert data[first["id"]]["failure"] == 1
    assert data[second["id"]]["success"] == 1


async def test_record_outcome_concurrent_writes(tmp_path):
    ml_model = AsyncMock()
    ml_model.update = AsyncMock()
    metrics_file = tmp_path / "metrics.json"
    router = AgentRouter(ml_model, metrics_path=metrics_file)
    agent = {
        "id": "agent_a",
        "skills": {"python"},
        "load": 0.1,
        "policies": set(),
        "status": "available",
    }
    task = {"required_skill": "python"}
    await asyncio.gather(*[router.record_outcome(task, agent, True) for _ in range(20)])
    data = json.loads(metrics_file.read_text())
    assert data[agent["id"]]["success"] == 20
