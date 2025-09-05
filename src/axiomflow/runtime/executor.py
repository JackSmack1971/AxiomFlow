"""Simple workflow execution engine with recovery integration."""

from __future__ import annotations

from typing import Any, Callable, Dict, List

from .recovery import RecoveryManager, RetryPolicy


class WorkflowExecutor:
    """Execute workflow steps with automatic recovery."""

    def __init__(self, recovery_manager: RecoveryManager | None = None) -> None:
        self.recovery_manager = recovery_manager or RecoveryManager()

    async def run_step(
        self,
        func: Callable[..., Any],
        *args: Any,
        retry_policy: RetryPolicy | None = None,
        compensation: Callable[[Exception], Any] | None = None,
        cleanup: Callable[[], Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Run a workflow step using the recovery manager."""
        return await self.recovery_manager.execute(
            func,
            *args,
            retry_policy=retry_policy,
            compensation=compensation,
            cleanup=cleanup,
            **kwargs,
        )

    async def run_workflow(
        self,
        workflow: Dict[str, Any],
        step_funcs: Dict[str, Callable[..., Any]],
        dry_run: bool = False,
    ) -> Dict[str, float]:
        """Execute all workflow steps respecting dependencies.

        Args:
            workflow: Parsed workflow dictionary.
            step_funcs: Mapping of step IDs to callables.
            dry_run: If ``True``, walk the graph without executing steps.

        Returns:
            Dictionary with actual ``runtime`` and ``cost`` totals.
        """
        order = self._topological_sort(workflow)
        total_runtime = 0.0
        total_cost = 0.0
        for step in order:
            sid = step["id"]
            func = step_funcs.get(sid)
            if dry_run:
                continue
            if func is None:
                raise ValueError(f"Missing function for step {sid}")
            result = await self.run_step(func)
            if isinstance(result, dict):
                total_runtime += float(result.get("runtime", 0.0))
                total_cost += float(result.get("cost", 0.0))
        return {"runtime": total_runtime, "cost": total_cost}

    def _topological_sort(self, workflow: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return workflow steps in dependency order.

        Args:
            workflow: Workflow dictionary.

        Returns:
            List of step dictionaries sorted topologically.
        """
        steps = {s["id"]: s for s in workflow.get("steps", [])}
        in_degree = {sid: 0 for sid in steps}
        for edge in workflow.get("edges", []):
            in_degree[edge["to"]] += 1
        queue = [sid for sid, deg in in_degree.items() if deg == 0]
        order: List[Dict[str, Any]] = []
        while queue:
            sid = queue.pop(0)
            order.append(steps[sid])
            for edge in workflow.get("edges", []):
                if edge["from"] == sid:
                    to = edge["to"]
                    in_degree[to] -= 1
                    if in_degree[to] == 0:
                        queue.append(to)
        if len(order) != len(steps):
            raise ValueError("Circular dependency detected")
        return order
