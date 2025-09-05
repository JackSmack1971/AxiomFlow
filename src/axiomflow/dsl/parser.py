"""Workflow DSL parser and loader."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Set

import yaml

logger = logging.getLogger(__name__)


@dataclass
class WorkflowParser:
    """Parser for workflow DSL definitions."""

    def parse(self, text: str) -> Dict[str, Any]:
        """Parse workflow DSL text into an AST.

        Args:
            text: YAML or JSON workflow definition.

        Returns:
            Parsed workflow dictionary.

        Raises:
            SyntaxError: If the input text is not valid YAML/JSON.
            ValueError: If semantic validation fails.
        """
        logger.debug("Parsing workflow DSL")
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as exc:  # pragma: no cover
            logger.error("Syntax error: %s", exc)
            raise SyntaxError("Invalid syntax") from exc
        if not isinstance(data, dict) or "workflow" not in data:
            logger.error("Missing workflow section")
            raise ValueError("Missing workflow section")
        workflow = data["workflow"]
        self._validate_schema(workflow)
        self._validate_semantics(workflow)
        workflow["resource_estimates"] = self._estimate_step_resources(workflow)
        workflow["estimates"] = self._estimate_totals(workflow)
        logger.debug("Workflow parsed successfully")
        return workflow

    def _validate_schema(self, workflow: Dict[str, Any]) -> None:
        """Validate required workflow fields.

        Args:
            workflow: Workflow dictionary.

        Raises:
            ValueError: If required fields are missing.
        """
        logger.debug("Validating workflow schema")
        required = {"name", "version", "personas", "steps", "edges", "gates"}
        missing = required - workflow.keys()
        if missing:
            logger.error("Missing fields: %s", missing)
            raise ValueError(f"Missing fields: {missing}")

    def _validate_semantics(self, workflow: Dict[str, Any]) -> None:
        """Validate semantic rules for workflow.

        Args:
            workflow: Workflow dictionary.

        Raises:
            ValueError: If semantic rules are violated.
        """
        logger.debug("Validating workflow semantics")
        personas = {p["id"] for p in workflow.get("personas", [])}
        gates = {g["id"] for g in workflow.get("gates", [])}
        workflow_inputs = {i["name"] for i in workflow.get("inputs", [])}
        produced: Dict[str, Set[str]] = {}
        for step in workflow.get("steps", []):
            sid = step["id"]
            persona = step.get("persona")
            if persona not in personas:
                logger.error("Unknown persona %s in step %s", persona, sid)
                raise ValueError(f"Unknown persona: {persona}")
            for gate in step.get("gates", []):
                if gate not in gates:
                    logger.error("Unknown gate %s in step %s", gate, sid)
                    raise ValueError(f"Unknown gate: {gate}")
            retry = step.get("retry")
            if retry:
                strategy = retry.get("backoff_strategy")
                if strategy not in {"linear", "exponential"}:
                    logger.error(
                        "Invalid backoff strategy %s in step %s", strategy, sid
                    )
                    raise ValueError("Invalid backoff strategy")
            for val in step.get("inputs", {}).values():
                if isinstance(val, str) and "." in val:
                    ref_step, output = val.split(".", 1)
                    if output not in produced.get(ref_step, set()):
                        logger.error("Unsatisfied input %s in step %s", val, sid)
                        raise ValueError("Unsatisfied input reference")
                elif isinstance(val, str):
                    if val not in workflow_inputs:
                        logger.error("Unsatisfied input %s in step %s", val, sid)
                        raise ValueError("Unsatisfied input reference")
            produced[sid] = set(step.get("outputs", {}).keys())
        self._check_cycles(workflow.get("edges", []))

    def _check_cycles(self, edges: List[Dict[str, str]]) -> None:
        """Check for circular dependencies in workflow edges.

        Args:
            edges: List of edge dictionaries.

        Raises:
            ValueError: If a cycle is detected.
        """
        logger.debug("Checking workflow edges for cycles")
        if not edges:
            return
        graph: Dict[str, List[str]] = {}
        for edge in edges:
            graph.setdefault(edge["from"], []).append(edge["to"])
        visited: Set[str] = set()
        stack: Set[str] = set()

        def visit(node: str) -> None:
            if node in stack:
                logger.error("Cycle detected at node %s", node)
                raise ValueError("Circular dependency detected")
            if node in visited:
                return
            stack.add(node)
            for nxt in graph.get(node, []):
                visit(nxt)
            stack.remove(node)
            visited.add(node)

        for start in list(graph):
            visit(start)

    def _estimate_step_resources(
        self, workflow: Dict[str, Any]
    ) -> Dict[str, Dict[str, float]]:
        """Compute CPU and memory estimates for each workflow step.

        Args:
            workflow: Workflow dictionary.

        Returns:
            Mapping of step IDs to ``{"cpu": float, "memory": float}``.
        """
        estimates: Dict[str, Dict[str, float]] = {}
        for step in workflow.get("steps", []):
            cpu = float(step.get("estimated_cpu", 0.0))
            memory = float(step.get("estimated_memory", 0.0))
            estimates[step["id"]] = {"cpu": cpu, "memory": memory}
        return estimates

    def _estimate_totals(self, workflow: Dict[str, Any]) -> Dict[str, float]:
        """Compute aggregate runtime and cost estimates for the workflow."""
        runtime = 0.0
        cost = 0.0
        for step in workflow.get("steps", []):
            runtime += float(step.get("estimated_runtime", 0.0))
            cost += float(step.get("estimated_cost", 0.0))
        return {"runtime": runtime, "cost": cost}


def _simulate_execution(workflow: Dict[str, Any]) -> List[str]:
    """Compute a topological execution order for the workflow steps.

    Args:
        workflow: Parsed workflow dictionary.

    Returns:
        List of step IDs in execution order.

    Raises:
        ValueError: If a circular dependency is detected.
    """
    steps = {s["id"] for s in workflow.get("steps", [])}
    graph: Dict[str, List[str]] = {sid: [] for sid in steps}
    indegree: Dict[str, int] = {sid: 0 for sid in steps}
    for edge in workflow.get("edges", []):
        graph[edge["from"]].append(edge["to"])
        indegree[edge["to"]] += 1
    order: List[str] = []
    queue: List[str] = [sid for sid, deg in indegree.items() if deg == 0]
    while queue:
        node = queue.pop(0)
        order.append(node)
        for nxt in graph[node]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    if len(order) != len(steps):  # pragma: no cover - safeguard
        raise ValueError("Circular dependency detected")
    return order


def parse_workflow(path: str, dry_run: bool = True) -> Dict[str, Any]:
    """Load and validate a workflow definition from disk.

    The workflow is loaded from ``path`` and converted into an AST. If
    ``dry_run`` is ``True`` the function also returns a simulated execution
    order without performing any side effects.

    Args:
        path: Path to a YAML or JSON workflow file.
        dry_run: When ``True`` simulate execution order without side effects.

    Returns:
        Parsed workflow dictionary augmented with resource estimates and,
        when ``dry_run`` is ``True``, an ``execution_order`` key.

    Raises:
        SyntaxError: If the file contains malformed YAML/JSON.
        ValueError: If semantic validation fails.
    """
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    parser = WorkflowParser()
    workflow = parser.parse(text)
    if dry_run:
        workflow["execution_order"] = _simulate_execution(workflow)
    return workflow
