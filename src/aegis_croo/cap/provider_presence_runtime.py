from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Protocol

from pydantic import BaseModel

from src.aegis_croo.cap.config import configured_provider_presence_enabled
from src.aegis_croo.cap.ws_safety import bounded_close, redact_sensitive_text


class ProviderPresenceStream(Protocol):
    async def close(self) -> None: ...


class ProviderPresenceClient(Protocol):
    async def connect_websocket(self) -> ProviderPresenceStream: ...

    async def close(self) -> None: ...


ClientFactory = Callable[[], ProviderPresenceClient]


class ProviderPresenceDisabledError(RuntimeError):
    pass


class ProviderPresenceResult(BaseModel):
    connected: bool
    closed: bool
    local_only: bool = True
    real_cap_ready: bool = False
    mutating_methods_called: bool = False
    error: str | None = None


class ProviderPresenceRuntime:
    """Hold one non-mutating CROO WebSocket connection open until externally stopped.

    No event handler of any kind is registered on the stream, and no CAP
    lifecycle method is referenced anywhere in this module. The only actions
    taken are ``connect_websocket()`` and ``close()``.
    """

    def __init__(self, *, client_factory: ClientFactory) -> None:
        self._client_factory = client_factory

    @classmethod
    def from_environment(cls, *, client_factory: ClientFactory) -> "ProviderPresenceRuntime":
        if not configured_provider_presence_enabled():
            raise ProviderPresenceDisabledError(
                "CAP_PROVIDER_PRESENCE_ENABLED must be true to start the "
                "persistent provider-presence runtime."
            )
        return cls(client_factory=client_factory)

    async def run(self, stop_event: asyncio.Event) -> ProviderPresenceResult:
        client = self._client_factory()
        stream: ProviderPresenceStream | None = None
        connected = False
        closed = True
        error: str | None = None
        try:
            stream = await client.connect_websocket()
            connected = True
            await stop_event.wait()
        except Exception as exc:  # noqa: BLE001
            error = redact_sensitive_text(str(exc))
        finally:
            if stream is not None:
                closed, close_error = await bounded_close(stream, timeout_seconds=5.0)
                if not closed and error is None:
                    error = close_error
            try:
                await client.close()
            except Exception:
                pass

        return ProviderPresenceResult(connected=connected, closed=closed, error=error)
