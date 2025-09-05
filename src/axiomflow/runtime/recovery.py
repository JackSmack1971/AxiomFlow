"""Recovery utilities for agent and tool execution."""

from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, List


@dataclass
class RetryPolicy:
    """Configuration for retry behaviour."""

    max_attempts: int = 3
    strategy: str = "exponential"
    base_delay: float = 0.1
    max_delay: float = 1.0

    def backoff(self, attempt: int) -> float:
        """Compute delay before the next attempt."""
        if self.strategy == "linear":
            delay = self.base_delay * attempt
        else:
            delay = self.base_delay * (2 ** (attempt - 1))
        return min(delay, self.max_delay)


async def _maybe_await(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Invoke ``func`` and await the result if needed."""
    result = func(*args, **kwargs)
    if inspect.isawaitable(result):
        return await result
    return result


class RecoveryManager:
    """Monitor errors and perform recovery actions."""

    def __init__(
        self,
        *,
        escalation_hook: (
            Callable[[List[Exception]], Awaitable[None] | None] | None
        ) = None,
    ) -> None:
        self.escalation_hook = escalation_hook
        self.errors: List[Exception] = []

    async def execute(
        self,
        func: Callable[..., Any],
        *args: Any,
        retry_policy: RetryPolicy | None = None,
        compensation: Callable[[Exception], Awaitable[None] | None] | None = None,
        cleanup: Callable[[], Awaitable[None] | None] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Execute ``func`` with retry and recovery logic."""
        policy = retry_policy or RetryPolicy()
        attempt = 0
        try:
            while True:
                try:
                    return await _maybe_await(func, *args, **kwargs)
                except Exception as exc:  # pragma: no cover - broad for recovery
                    self.errors.append(exc)
                    attempt += 1
                    if compensation:
                        await _maybe_await(compensation, exc)
                    if attempt >= policy.max_attempts:
                        raise
                    await asyncio.sleep(policy.backoff(attempt))
        except Exception:
            if self.escalation_hook:
                await _maybe_await(self.escalation_hook, self.errors)
            raise
        finally:
            if cleanup:
                await _maybe_await(cleanup)
