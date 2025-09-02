"""Workflow DSL parser."""

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
        """Parse workflow DSL text.

        Args:
            text: YAML or JSON workflow definition.

        Returns:
            Parsed workflow dictionary.

        Raises:
            ValueError: If the workflow is invalid.
        """
        logger.debug("Parsing workflow DSL")
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as exc:  # pragma: no cover
            logger.error("Syntax error: %s", exc)
            raise ValueError("Invalid syntax") from exc
        if not isinstance(data, dict) or "workflow" not in data:
            logger.error("Missing workflow section")
            raise ValueError("Missing workflow section")
        workflow = data["workflow"]
        self._validate_schema(workflow)
        self._validate_semantics(workflow)
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
