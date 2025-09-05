import asyncio

import pytest

from axiomflow.runtime.recovery import RecoveryManager, RetryPolicy


def test_recovery_manager_retries_and_cleans_up():
    async def runner():
        attempts = 0
        compensation_calls = []
        cleaned = False

        async def flaky():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError("boom")
            return "ok"

        async def compensation(exc: Exception) -> None:
            compensation_calls.append(type(exc))

        async def cleanup() -> None:
            nonlocal cleaned
            cleaned = True

        manager = RecoveryManager()
        policy = RetryPolicy(max_attempts=5, strategy="linear", base_delay=0)
        result = await manager.execute(
            flaky, compensation=compensation, cleanup=cleanup, retry_policy=policy
        )

        assert result == "ok"
        assert len(compensation_calls) == 2
        assert cleaned

    asyncio.run(runner())


def test_recovery_manager_escalates_after_failures():
    async def runner():
        escalated = False

        async def always_fail():
            raise RuntimeError("nope")

        async def escalate(errors):
            nonlocal escalated
            escalated = True

        manager = RecoveryManager(escalation_hook=escalate)
        policy = RetryPolicy(max_attempts=2, base_delay=0)

        with pytest.raises(RuntimeError):
            await manager.execute(always_fail, retry_policy=policy)

        assert escalated

    asyncio.run(runner())
