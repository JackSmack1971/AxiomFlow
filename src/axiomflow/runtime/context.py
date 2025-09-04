"""Context management utilities for agent handoffs."""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any, Awaitable, Callable, Mapping

from cryptography.fernet import Fernet


@dataclass(frozen=True)
class Context:
    """Immutable container for handoff context data."""

    data: Mapping[str, Any]
    hash: str

    @staticmethod
    def create(data: Mapping[str, Any]) -> "Context":
        """Create a context from a mapping, computing its integrity hash."""
        serialised = json.dumps(dict(data), sort_keys=True).encode("utf-8")
        digest = hashlib.sha256(serialised).hexdigest()
        return Context(data=MappingProxyType(dict(data)), hash=digest)


class ContextManager:
    """Handles secure context handoffs between agents."""

    def __init__(self, key: bytes, allowed_recipients: set[str] | None = None) -> None:
        self.fernet = Fernet(key)
        self.allowed_recipients = allowed_recipients or set()
        self.audit_log: list[dict[str, str]] = []
        self._lock = asyncio.Lock()

    def _audit(self, event: str, recipient: str | None = None) -> None:
        self.audit_log.append(
            {
                "event": event,
                "recipient": recipient or "",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def serialize(self, context: Context) -> bytes:
        """Serialize context to deterministic JSON bytes."""
        return json.dumps(
            dict(context.data), sort_keys=True, separators=(",", ":")
        ).encode("utf-8")

    def deserialize(self, payload: bytes, expected_hash: str) -> Context:
        """Deserialize payload and verify integrity using expected hash."""
        data = json.loads(payload.decode("utf-8"))
        if self._hash(data) != expected_hash:
            raise ValueError("hash mismatch")
        return Context.create(data)

    async def handoff_context(
        self,
        context: Context,
        recipient: str,
        *,
        transmit: Callable[[bytes], Awaitable[bytes]] | None = None,
        timeout: float = 0.2,
    ) -> Context:
        """Transfer context to another agent securely.

        Args:
            context: The context to hand off.
            recipient: Identifier of the receiving agent.
            transmit: Coroutine simulating network transmission.
            timeout: Maximum time in seconds allowed for the handoff.

        Returns:
            The context received after transfer.
        """
        if recipient not in self.allowed_recipients:
            self._audit("rejected", recipient)
            raise ValueError("invalid recipient")

        async with self._lock:
            self._audit("handoff_start", recipient)
            payload = self.serialize(context)
            ciphertext = self.fernet.encrypt(payload)

            async def _default_transmit(data: bytes) -> bytes:
                return data

            transmit = transmit or _default_transmit
            start = time.perf_counter()
            try:
                returned = await asyncio.wait_for(transmit(ciphertext), timeout=timeout)
            except asyncio.TimeoutError as exc:
                self._audit("timeout", recipient)
                raise TimeoutError("handoff timeout") from exc

            try:
                decrypted = self.fernet.decrypt(returned)
            except (
                Exception
            ) as exc:  # pragma: no cover - cryptography raises many types
                self._audit("integrity_failure", recipient)
                raise ValueError("context corruption") from exc

            result = self.deserialize(decrypted, context.hash)
            if dict(result.data) != dict(context.data):
                self._audit("fidelity_failure", recipient)
                raise ValueError("context fidelity failure")

            duration_ms = (time.perf_counter() - start) * 1000
            if duration_ms > timeout * 1000:
                self._audit("timeout", recipient)
                raise TimeoutError("handoff timeout")

            self._audit("handoff_complete", recipient)
            return result

    def _hash(self, data: Mapping[str, Any]) -> str:
        """Generate SHA-256 hash for provided mapping."""
        return hashlib.sha256(
            json.dumps(dict(data), sort_keys=True).encode("utf-8")
        ).hexdigest()


async def handoff_context(
    manager: ContextManager,
    context: Context,
    recipient: str,
    **kwargs: Any,
) -> Context:
    """Convenience wrapper around :meth:`ContextManager.handoff_context`."""
    return await manager.handoff_context(context, recipient, **kwargs)
