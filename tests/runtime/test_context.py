import asyncio
import time

import pytest
from cryptography.fernet import Fernet

from axiomflow.runtime.context import Context, ContextManager

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def manager() -> ContextManager:
    key = Fernet.generate_key()
    return ContextManager(key, {"agent_alpha", "agent_beta"})


def test_context_immutable():
    ctx = Context.create({"foo": "bar"})
    with pytest.raises(TypeError):
        ctx.data["foo"] = "baz"


def test_serialization_roundtrip(manager: ContextManager):
    ctx = Context.create({"user": "alice", "level": 5})
    payload = manager.serialize(ctx)
    restored = manager.deserialize(payload, ctx.hash)
    assert restored.data == ctx.data
    assert restored.hash == ctx.hash


async def test_handoff_success(manager: ContextManager):
    ctx = Context.create({"user": "alice", "value": 42})
    captured = {}

    async def transmit(payload: bytes) -> bytes:
        captured["ciphertext"] = payload
        return payload

    start = time.perf_counter()
    result = await manager.handoff_context(ctx, "agent_alpha", transmit=transmit)
    duration = (time.perf_counter() - start) * 1000

    assert duration < 200
    assert result.data == ctx.data
    assert result.hash == ctx.hash
    assert captured["ciphertext"] != manager.serialize(ctx)
    assert any(e["event"] == "handoff_complete" for e in manager.audit_log)


async def test_timeout(manager: ContextManager):
    ctx = Context.create({"a": 1})

    async def slow(payload: bytes) -> bytes:
        await asyncio.sleep(0.3)
        return payload

    with pytest.raises(TimeoutError):
        await manager.handoff_context(ctx, "agent_alpha", transmit=slow)


async def test_corruption_detected(manager: ContextManager):
    ctx = Context.create({"a": 1})

    async def corrupt(payload: bytes) -> bytes:
        data = bytearray(payload)
        data[10] ^= 0xFF
        return bytes(data)

    with pytest.raises(ValueError):
        await manager.handoff_context(ctx, "agent_alpha", transmit=corrupt)


async def test_invalid_recipient(manager: ContextManager):
    ctx = Context.create({"a": 1})
    with pytest.raises(ValueError):
        await manager.handoff_context(ctx, "unknown")
