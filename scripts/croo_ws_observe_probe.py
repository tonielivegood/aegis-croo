from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.aegis_croo.cap.config import (
    configured_cap_mode,
    configured_real_provider_enabled,
    configured_ws_observe_enabled,
    configured_ws_observe_timeout_seconds,
)
from src.aegis_croo.cap.ws_observe_harness import (
    ObserveOnlyResult,
    ObserveOnlyStream,
    ObserveOnlyWebSocketHarness,
    SanitizedEventSummary,
    redact_sensitive_text,
)


MAX_PROBE_SECONDS = 5.0
StreamFactory = Callable[[str, str], ObserveOnlyStream]
ProbeStatus = Literal["verified_observe_only", "observe_abort", "failed"]


class ProbePreflightError(RuntimeError):
    pass


class ProbeReport(BaseModel):
    probe_status: ProbeStatus
    websocket_connection_status: ProbeStatus
    agent_online_status: Literal[
        "observed_connection_only",
        "not_observed",
    ]
    real_cap_ready: Literal[False] = False
    closed: bool
    mutating_methods_called: Literal[False] = False
    event: SanitizedEventSummary | None = None
    failure_reason: str | None = None


class RedactingLogFilter(logging.Filter):
    def __init__(self, sensitive_values: list[str]) -> None:
        super().__init__()
        self._sensitive_values = [value for value in sensitive_values if value]

    def filter(self, record: logging.LogRecord) -> bool:
        message = redact_sensitive_text(record.getMessage())
        for value in self._sensitive_values:
            message = message.replace(value, "[REDACTED]")
        record.msg = message
        record.args = ()
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
        return True


async def run_probe(
    *,
    stream_factory: StreamFactory | None = None,
) -> ProbeReport:
    sdk_key, service_id, ws_url, timeout_seconds = _load_probe_config()
    _configure_sanitized_logging([sdk_key, service_id])

    factory = stream_factory or _create_sdk_stream
    try:
        stream = factory(sdk_key, ws_url)
    except Exception:
        return _failed_report("stream_initialization_failed", closed=False)

    harness = ObserveOnlyWebSocketHarness(
        enabled=True,
        timeout_seconds=timeout_seconds,
    )
    result = await harness.run(stream, _connect_stream)
    return _report_from_harness(result)


def _load_probe_config() -> tuple[str, str, str, float]:
    if configured_cap_mode() != "mock":
        raise ProbePreflightError("CAP_MODE must remain mock for this probe.")
    if configured_real_provider_enabled():
        raise ProbePreflightError(
            "CAP_REAL_PROVIDER_ENABLED must remain false for this probe."
        )
    if not configured_ws_observe_enabled():
        raise ProbePreflightError(
            "CAP_WS_OBSERVE_ONLY_ENABLED must be true for the manual probe."
        )

    timeout_seconds = configured_ws_observe_timeout_seconds()
    if timeout_seconds > MAX_PROBE_SECONDS:
        raise ProbePreflightError(
            "CAP_WS_OBSERVE_TIMEOUT_SECONDS must be at most 5."
        )

    required = {
        "CROO_SDK_KEY": os.getenv("CROO_SDK_KEY") or "",
        "CROO_SERVICE_ID": os.getenv("CROO_SERVICE_ID") or "",
        "CROO_WS_URL": os.getenv("CROO_WS_URL") or "",
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise ProbePreflightError(
            "Missing required environment variables: " + ", ".join(missing)
        )

    ws_url = required["CROO_WS_URL"]
    parsed = urlparse(ws_url)
    if (
        parsed.scheme != "wss"
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ProbePreflightError(
            "CROO_WS_URL must be a credential-free wss URL."
        )

    return (
        required["CROO_SDK_KEY"],
        required["CROO_SERVICE_ID"],
        ws_url,
        timeout_seconds,
    )


def _configure_sanitized_logging(sensitive_values: list[str]) -> None:
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.WARNING)
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    handler.addFilter(RedactingLogFilter(sensitive_values))

    for logger_name in ("croo", "websockets"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
        logger.propagate = False


def _create_sdk_stream(sdk_key: str, ws_url: str) -> ObserveOnlyStream:
    croo_sdk = import_module("croo")
    return croo_sdk.EventStream(sdk_key, ws_url)


async def _connect_stream(stream: ObserveOnlyStream) -> None:
    connect = getattr(stream, "connect")
    await connect()


def _report_from_harness(result: ObserveOnlyResult) -> ProbeReport:
    if result.status == "timed_out" and result.connected and result.closed:
        return ProbeReport(
            probe_status="verified_observe_only",
            websocket_connection_status="verified_observe_only",
            agent_online_status="observed_connection_only",
            closed=True,
        )
    if result.status == "event_aborted":
        return ProbeReport(
            probe_status="observe_abort",
            websocket_connection_status="observe_abort",
            agent_online_status=(
                "observed_connection_only" if result.connected else "not_observed"
            ),
            closed=result.closed,
            event=result.event,
            failure_reason="business_event_observed",
        )
    return _failed_report(
        _failure_reason(result),
        closed=result.closed,
        event=result.event,
    )


def _failure_reason(result: ObserveOnlyResult) -> str:
    if result.status == "close_failed":
        return "stream_close_failed"
    if result.status == "timed_out" and not result.connected:
        return "connection_timeout"
    if result.status == "error":
        return "connection_error"
    return "probe_failed"


def _failed_report(
    reason: str,
    *,
    closed: bool,
    event: SanitizedEventSummary | None = None,
) -> ProbeReport:
    return ProbeReport(
        probe_status="failed",
        websocket_connection_status="failed",
        agent_online_status="not_observed",
        closed=closed,
        event=event,
        failure_reason=reason,
    )


def main() -> int:
    try:
        report = asyncio.run(run_probe())
    except ProbePreflightError as exc:
        payload: dict[str, Any] = {
            "probe_status": "failed",
            "websocket_connection_status": "failed",
            "agent_online_status": "not_observed",
            "real_cap_ready": False,
            "failure_reason": redact_sensitive_text(str(exc)),
        }
        sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")
        return 1

    sys.stdout.write(report.model_dump_json() + "\n")
    if report.probe_status == "verified_observe_only":
        return 0
    if report.probe_status == "observe_abort":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
