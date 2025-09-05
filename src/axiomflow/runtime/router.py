from __future__ import annotations

import inspect
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

from axiomflow.logging import request_id_var

logger = logging.getLogger(__name__)


class RoutingError(Exception):
    """Base class for routing exceptions."""


class NoAgentsAvailableError(RoutingError):
    """Raised when no agents are available for routing."""


class PolicyViolationError(RoutingError):
    """Raised when a candidate agent violates routing policies."""


@dataclass
class Agent:
    """Simple representation of an agent."""

    id: str
    skills: set[str]
    load: float
    policies: set[str]
    status: str = "available"


class AgentRouter:
    """Hybrid rule-based and ML-driven agent router."""

    def __init__(
        self,
        ml_model: Any,
        *,
        metrics_hook: Optional[Callable[[float], None]] = None,
        metrics_path: Optional[str] = None,
    ) -> None:
        self._ml_model = ml_model
        self._metrics_hook = metrics_hook
        self._cb_threshold = 3
        self._failure_count = 0
        self._use_ml = True
        self._metrics_path = Path(metrics_path) if metrics_path else None
        self._metrics: Dict[str, Dict[str, int]] = {}
        if self._metrics_path and self._metrics_path.exists():
            try:
                self._metrics = json.loads(self._metrics_path.read_text())
            except Exception:  # pragma: no cover - corrupt metrics
                self._metrics = {}

    async def route_task(
        self,
        task: Dict[str, Any],
        agents: Iterable[Dict[str, Any]],
        *,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Route a task to the most suitable agent."""
        if correlation_id:
            request_id_var.set(correlation_id)
        start = time.perf_counter()
        candidates = self._filter_agents(task, agents)
        if not candidates:
            raise NoAgentsAvailableError("no agents meet requirements")
        try:
            if self._use_ml:
                agent = await self._ml_select(task, candidates)
                self._failure_count = 0
            else:  # circuit breaker open
                agent = min(candidates, key=lambda a: a["load"])
        except Exception:  # pragma: no cover - fallback path
            self._failure_count += 1
            if self._failure_count >= self._cb_threshold:
                self._use_ml = False
            logger.warning("ML model unavailable, falling back to rule-based scoring")
            agent = min(candidates, key=lambda a: a["load"])
        duration_ms = (time.perf_counter() - start) * 1000
        if self._metrics_hook:
            self._metrics_hook(duration_ms)
        if duration_ms > 150:
            logger.warning(
                "routing exceeded latency threshold", extra={"duration_ms": duration_ms}
            )
        else:
            logger.info("routing completed", extra={"duration_ms": duration_ms})
        return agent

    def _filter_agents(
        self, task: Dict[str, Any], agents: Iterable[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        required = task.get("required_skill")
        disallowed = task.get("disallowed_policies", set())
        candidates = []
        for agent in agents:
            if agent.get("status") != "available":
                continue
            if agent.get("load", 1.0) >= 0.8:
                continue
            if required and required not in agent.get("skills", set()):
                continue
            if disallowed & agent.get("policies", set()):
                raise PolicyViolationError("policy violation")
            candidates.append(agent)
        return candidates

    async def _ml_select(
        self, task: Dict[str, Any], candidates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        scores = []
        for agent in candidates:
            features = {
                "agent_id": agent["id"],
                "task": task,
                "load": agent.get("load", 0.0),
            }
            score = await self._ml_model.score(features)
            scores.append((score, agent))
        scores.sort(key=lambda x: x[0], reverse=True)
        return scores[0][1]

    async def record_outcome(
        self, task: Dict[str, Any], agent: Dict[str, Any], success: bool
    ) -> None:
        """Record the result of a routed task and update learning state."""
        features = {
            "agent_id": agent["id"],
            "task": task,
            "result": success,
        }
        update = getattr(self._ml_model, "update", None)
        if update:
            res = update(features)
            if inspect.isawaitable(res):
                await res
        if self._metrics_path:
            entry = self._metrics.setdefault(agent["id"], {"success": 0, "failure": 0})
            if success:
                entry["success"] += 1
            else:
                entry["failure"] += 1
            self._metrics_path.write_text(json.dumps(self._metrics))
