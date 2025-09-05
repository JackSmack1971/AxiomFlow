"""Simple workflow execution engine with recovery integration."""

from __future__ import annotations

from typing import Any, Callable

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
