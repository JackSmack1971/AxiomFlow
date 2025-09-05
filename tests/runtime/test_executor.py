import asyncio

from axiomflow.runtime.executor import WorkflowExecutor
from axiomflow.runtime.recovery import RetryPolicy


def test_executor_uses_recovery_manager():
    async def runner():
        attempts = 0

        async def flaky():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise ValueError("fail")
            return "done"

        executor = WorkflowExecutor()
        policy = RetryPolicy(max_attempts=3, base_delay=0)
        result = await executor.run_step(flaky, retry_policy=policy)
        assert result == "done"

    asyncio.run(runner())
