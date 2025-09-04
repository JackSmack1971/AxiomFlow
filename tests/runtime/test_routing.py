from typing import List
from unittest.mock import AsyncMock

import pytest

from axiomflow.runtime.router import (
    AgentRouter,
    NoAgentsAvailableError,
    PolicyViolationError,
)

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
