from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable, Callable, Mapping
from typing import Any, Literal, Protocol

from pydantic import BaseModel

from src.aegis_croo.cap.config import (
    configured_ws_observe_enabled,
    configured_ws_observe_timeout_seconds,
)


REDACTED = "[REDACTED]"
REDACTED_WEBSOCKET_URL = "[REDACTED_WEBSOCKET_URL]"
_CROO_KEY_PATTERN = re.compile(r"croo_sk_[a-z0-9._-]+", re.IGNORECASE)
_CREDENTIAL_WS_URL_PATTERN = re.compile(
    r"\bwss?://[^\s\"']*(?:\?|@)[^\s\"']*",
    re.IGNORECASE,
)
_CREDENTIAL_PARAMETER_PATTERN = re.compile(
    r"(\b(?:key|sdk[_-]?key|api[_-]?key|token)\s*=\s*)[^\s&#,;]+",
    re.IGNORECASE,
)
_CREDENTIAL_HEADER_PATTERN = re.compile(
    r"(\b(?:x-sdk-key|authorization|proxy-authorization)\b\s*[:=]\s*)"
    r"[^\r\n,;]+",
    re.IGNORECASE,
)
_SENSITIVE_HEADER_NAMES = {
    "authorization",
    "proxy-authorization",
    "x-api-key",
    "x-sdk-key",
}
_KNOWN_EVENT_TYPES = {
    "order_negotiation_created",
    "order_negotiation_rejected",
    "order_negotiation_expired",
    "order_created",
    "order_paid",
    "order_completed",
    "order_rejected",
    "order_expired",
}


class ObserveOnlyStream(Protocol):
    def on_any(self, handler: Callable[[Any], None]) -> None: ...

    async def close(self) -> None: ...


ObserveConnector = Callable[[ObserveOnlyStream], Awaitable[None]]
ObserveStatus = Literal["timed_out", "event_aborted", "error", "close_failed"]


class SanitizedEventSummary(BaseModel):
    event_type: str
    has_negotiation_id: bool
    has_order_id: bool


class ObserveOnlyResult(BaseModel):
    status: ObserveStatus
    local_only: Literal[True] = True
    real_cap_ready: Literal[False] = False
    close_attempted: Literal[True] = True
    closed: bool
    event: SanitizedEventSummary | None = None
    error: str | None = None


class ObserveOnlyDisabledError(RuntimeError):
    pass


class ObserveOnlyWebSocketHarness:
    def __init__(
        self,
        *,
        enabled: bool,
        timeout_seconds: float,
        close_timeout_seconds: float = 1.0,
    ) -> None:
        self._enabled = enabled
        self._timeout_seconds = timeout_seconds
        self._close_timeout_seconds = close_timeout_seconds

    @classmethod
    def from_environment(cls) -> "ObserveOnlyWebSocketHarness":
        return cls(
            enabled=configured_ws_observe_enabled(),
            timeout_seconds=configured_ws_observe_timeout_seconds(),
        )

    async def run(
        self,
        stream: ObserveOnlyStream,
        connect: ObserveConnector,
    ) -> ObserveOnlyResult:
        if not self._enabled:
            raise ObserveOnlyDisabledError(
                "Observe-only WebSocket harness is disabled."
            )

        loop = asyncio.get_running_loop()
        event_future: asyncio.Future[SanitizedEventSummary] = loop.create_future()

        def on_event(event: Any) -> None:
            summary = _sanitize_event(event)

            def set_summary() -> None:
                if not event_future.done():
                    event_future.set_result(summary)

            loop.call_soon_threadsafe(set_summary)

        status: ObserveStatus = "error"
        event: SanitizedEventSummary | None = None
        error: str | None = None
        connect_task: asyncio.Task[None] | None = None

        try:
            stream.on_any(on_event)
            connect_task = asyncio.create_task(connect(stream))
            event = await asyncio.wait_for(
                _wait_for_connection_or_event(connect_task, event_future),
                timeout=self._timeout_seconds,
            )
            status = "event_aborted"
        except TimeoutError:
            status = "timed_out"
        except Exception as exc:
            status = "error"
            error = redact_sensitive_text(str(exc))
        finally:
            if connect_task and not connect_task.done():
                connect_task.cancel()
                await asyncio.gather(connect_task, return_exceptions=True)

        closed = False
        try:
            await asyncio.wait_for(
                stream.close(),
                timeout=self._close_timeout_seconds,
            )
            closed = True
        except Exception as exc:
            status = "close_failed"
            error = redact_sensitive_text(str(exc))

        return ObserveOnlyResult(
            status=status,
            closed=closed,
            event=event,
            error=error,
        )


async def _wait_for_connection_or_event(
    connect_task: asyncio.Task[None],
    event_future: asyncio.Future[SanitizedEventSummary],
) -> SanitizedEventSummary:
    done, _ = await asyncio.wait(
        {connect_task, event_future},
        return_when=asyncio.FIRST_COMPLETED,
    )
    if event_future in done:
        return event_future.result()
    await connect_task
    return await event_future


def redact_sensitive_text(value: str) -> str:
    redacted = _CREDENTIAL_WS_URL_PATTERN.sub(REDACTED_WEBSOCKET_URL, value)
    redacted = _CREDENTIAL_HEADER_PATTERN.sub(
        lambda match: f"{match.group(1)}{REDACTED}",
        redacted,
    )
    redacted = _CREDENTIAL_PARAMETER_PATTERN.sub(
        lambda match: f"{match.group(1)}{REDACTED}",
        redacted,
    )
    return _CROO_KEY_PATTERN.sub(REDACTED, redacted)


def redact_headers(headers: Mapping[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for name, value in headers.items():
        if name.casefold() in _SENSITIVE_HEADER_NAMES:
            result[name] = REDACTED
        else:
            result[name] = redact_sensitive_text(str(value))
    return result


def _sanitize_event(event: Any) -> SanitizedEventSummary:
    event_type = str(_event_value(event, "type") or "")
    safe_event_type = (
        event_type if event_type in _KNOWN_EVENT_TYPES else "unknown_event"
    )
    return SanitizedEventSummary(
        event_type=safe_event_type,
        has_negotiation_id=bool(_event_value(event, "negotiation_id")),
        has_order_id=bool(_event_value(event, "order_id")),
    )


def _event_value(event: Any, name: str) -> Any:
    if isinstance(event, Mapping):
        return event.get(name)
    return getattr(event, name, None)
