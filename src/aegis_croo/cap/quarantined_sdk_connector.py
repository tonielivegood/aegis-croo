from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field

from src.aegis_croo.cap.option_b_pilot_runner import (
    OptionBNegotiationPilotRequest,
    OptionBNegotiationPilotResult,
    OptionBNegotiationPilotRunner,
)
from src.aegis_croo.cap.pilot_readiness import PilotRunIDLookup
from src.aegis_croo.cap.ws_safety import bounded_close, redact_sensitive_text


QuarantinedConnectorStatus = Literal[
    "no_go",
    "separate_approval_required",
    "manual_review",
    "timed_out",
    "setup_failed",
    "registration_failed",
    "stream_error",
    "close_failed",
]

_NEGOTIATION_EVENT_TYPE = "order_negotiation_created"
_ALLOWED_EVENT_KEYS = {
    "type",
    "service_id",
    "serviceId",
    "service_name",
    "serviceName",
    "requirements_type",
    "requirementsType",
    "requirements",
    "require_fund_transfer",
    "requires_fund_transfer",
    "fund_transfer_required",
    "requiresFundTransfer",
    "requireFundTransfer",
    "fundTransferRequired",
}
_SENSITIVE_NESTED_KEYS = {
    "authorization",
    "proxy-authorization",
    "x-api-key",
    "x-sdk-key",
    "api_key",
    "sdk_key",
    "callback_url",
    "websocket_url",
    "negotiation_id",
    "order_id",
}


class QuarantinedNegotiationStream(Protocol):
    def on_any(self, handler: Callable[[Any], None]) -> None: ...

    async def start(self) -> None: ...

    async def close(self) -> None: ...


class QuarantinedSDKClient(Protocol):
    async def open_negotiation_stream(
        self,
    ) -> QuarantinedNegotiationStream: ...


SDKLoader = Callable[[], QuarantinedSDKClient]


class OptionBRunner(Protocol):
    def prepare(
        self,
        request: OptionBNegotiationPilotRequest,
        *,
        run_registry: PilotRunIDLookup | None = None,
    ) -> OptionBNegotiationPilotResult: ...

    async def simulate_negotiation(
        self,
        request: OptionBNegotiationPilotRequest,
        *,
        event: Mapping[str, Any],
        run_registry: PilotRunIDLookup | None = None,
    ) -> OptionBNegotiationPilotResult: ...


class QuarantinedConnectorRequest(BaseModel):
    pilot: OptionBNegotiationPilotRequest = Field(
        default_factory=OptionBNegotiationPilotRequest
    )
    sdk_load_authorized: bool = False


class QuarantinedConnectorResult(BaseModel):
    status: QuarantinedConnectorStatus
    reason_codes: list[str] = Field(default_factory=list)
    sdk_load_attempted: bool = False
    sdk_loaded: bool = False
    stream_start_attempted: bool = False
    event_received: bool = False
    close_attempted: bool = False
    closed: bool = False
    runner_result: OptionBNegotiationPilotResult | None = None
    local_only: Literal[True] = True
    manual_review_only: Literal[True] = True
    live_execution_authorized: Literal[False] = False
    mutating_methods_called: Literal[False] = False
    real_cap_ready: Literal[False] = False
    error: str | None = None


class QuarantinedSDKNegotiationConnector:
    """Lazy, injected SDK boundary with no import-time or startup behavior."""

    def __init__(
        self,
        *,
        sdk_loader: SDKLoader,
        runner: OptionBRunner | None = None,
    ) -> None:
        self._sdk_loader = sdk_loader
        self._runner = runner or OptionBNegotiationPilotRunner()

    async def run(
        self,
        request: QuarantinedConnectorRequest,
        *,
        run_registry: PilotRunIDLookup | None = None,
    ) -> QuarantinedConnectorResult:
        prepared = self._runner.prepare(
            request.pilot,
            run_registry=run_registry,
        )
        if prepared.status != "manual_review_plan_ready":
            status: QuarantinedConnectorStatus = (
                "separate_approval_required"
                if prepared.status == "separate_approval_required"
                else "no_go"
            )
            return QuarantinedConnectorResult(
                status=status,
                reason_codes=list(prepared.reason_codes),
            )
        if not request.sdk_load_authorized:
            return QuarantinedConnectorResult(
                status="no_go",
                reason_codes=["sdk_load_not_authorized"],
            )

        plan = prepared.connection_plan
        if plan is None:
            return QuarantinedConnectorResult(
                status="no_go",
                reason_codes=["missing_connection_plan"],
            )

        try:
            client = self._sdk_loader()
        except Exception as exc:
            return QuarantinedConnectorResult(
                status="setup_failed",
                sdk_load_attempted=True,
                error=redact_sensitive_text(str(exc)),
            )

        try:
            stream = await client.open_negotiation_stream()
        except Exception as exc:
            return QuarantinedConnectorResult(
                status="setup_failed",
                sdk_load_attempted=True,
                sdk_loaded=True,
                error=redact_sensitive_text(str(exc)),
            )

        result = QuarantinedConnectorResult(
            status="stream_error",
            sdk_load_attempted=True,
            sdk_loaded=True,
        )
        start_task: asyncio.Task[None] | None = None
        try:
            loop = asyncio.get_running_loop()
            queue: asyncio.Queue[Any] = asyncio.Queue(maxsize=1)

            def on_event(event: Any) -> None:
                def put_once() -> None:
                    if queue.empty():
                        queue.put_nowait(event)

                loop.call_soon_threadsafe(put_once)

            try:
                stream.on_any(on_event)
            except Exception as exc:
                result = QuarantinedConnectorResult(
                    status="registration_failed",
                    sdk_load_attempted=True,
                    sdk_loaded=True,
                    error=redact_sensitive_text(str(exc)),
                )
            else:
                start_task = asyncio.create_task(stream.start())
                result = await self._wait_for_one_event(
                    request,
                    stream=stream,
                    start_task=start_task,
                    queue=queue,
                    run_registry=run_registry,
                )
        except Exception as exc:
            result = QuarantinedConnectorResult(
                status="stream_error",
                sdk_load_attempted=True,
                sdk_loaded=True,
                stream_start_attempted=start_task is not None,
                error=redact_sensitive_text(str(exc)),
            )
        finally:
            if start_task is not None and not start_task.done():
                start_task.cancel()
                await asyncio.gather(start_task, return_exceptions=True)

        closed, close_error = await bounded_close(
            stream,
            timeout_seconds=plan.close_timeout_seconds,
        )
        updates: dict[str, Any] = {
            "close_attempted": True,
            "closed": closed,
        }
        if not closed:
            updates.update(status="close_failed", error=close_error)
        return result.model_copy(update=updates)

    async def _wait_for_one_event(
        self,
        request: QuarantinedConnectorRequest,
        *,
        stream: QuarantinedNegotiationStream,
        start_task: asyncio.Task[None],
        queue: asyncio.Queue[Any],
        run_registry: PilotRunIDLookup | None,
    ) -> QuarantinedConnectorResult:
        plan = self._runner.prepare(
            request.pilot,
            run_registry=run_registry,
        ).connection_plan
        if plan is None:
            return QuarantinedConnectorResult(
                status="no_go",
                reason_codes=["missing_connection_plan"],
                sdk_load_attempted=True,
                sdk_loaded=True,
                stream_start_attempted=True,
            )

        loop = asyncio.get_running_loop()
        deadline = loop.time() + plan.runtime_timeout_seconds
        while True:
            stream_error = _stream_error(stream)
            if stream_error is not None:
                return QuarantinedConnectorResult(
                    status="stream_error",
                    sdk_load_attempted=True,
                    sdk_loaded=True,
                    stream_start_attempted=True,
                    error=stream_error,
                )
            if start_task.done():
                start_error = _task_error(start_task)
                if start_error is not None:
                    return QuarantinedConnectorResult(
                        status="stream_error",
                        sdk_load_attempted=True,
                        sdk_loaded=True,
                        stream_start_attempted=True,
                        error=start_error,
                    )
            remaining = deadline - loop.time()
            if remaining <= 0:
                return QuarantinedConnectorResult(
                    status="timed_out",
                    reason_codes=["event_timeout"],
                    sdk_load_attempted=True,
                    sdk_loaded=True,
                    stream_start_attempted=True,
                )
            try:
                event = await asyncio.wait_for(
                    queue.get(), timeout=min(0.01, remaining)
                )
            except TimeoutError:
                if start_task.done() and start_task.exception() is None:
                    return QuarantinedConnectorResult(
                        status="stream_error",
                        reason_codes=["stream_ended_without_event"],
                        sdk_load_attempted=True,
                        sdk_loaded=True,
                        stream_start_attempted=True,
                    )
                continue
            return await self._route_event(
                request,
                event=event,
                run_registry=run_registry,
            )

    async def _route_event(
        self,
        request: QuarantinedConnectorRequest,
        *,
        event: Any,
        run_registry: PilotRunIDLookup | None,
    ) -> QuarantinedConnectorResult:
        if not isinstance(event, Mapping) or event.get("type") != _NEGOTIATION_EVENT_TYPE:
            return QuarantinedConnectorResult(
                status="no_go",
                reason_codes=["unsupported_event_type"],
                sdk_load_attempted=True,
                sdk_loaded=True,
                stream_start_attempted=True,
                event_received=True,
            )
        sanitized_event = _sanitize_negotiation_event(event)
        runner_result = await self._runner.simulate_negotiation(
            request.pilot,
            event=sanitized_event,
            run_registry=run_registry,
        )
        if runner_result.status != "manual_review_simulated":
            return QuarantinedConnectorResult(
                status="no_go",
                reason_codes=list(runner_result.reason_codes),
                sdk_load_attempted=True,
                sdk_loaded=True,
                stream_start_attempted=True,
                event_received=True,
                runner_result=runner_result,
            )
        return QuarantinedConnectorResult(
            status="manual_review",
            reason_codes=list(runner_result.reason_codes),
            sdk_load_attempted=True,
            sdk_loaded=True,
            stream_start_attempted=True,
            event_received=True,
            runner_result=runner_result,
        )


def _sanitize_negotiation_event(event: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: _sanitize_value(value)
        for key, value in event.items()
        if key in _ALLOWED_EVENT_KEYS
    }


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_sensitive_text(value)
    if isinstance(value, Mapping):
        return {
            str(key): _sanitize_value(item)
            for key, item in value.items()
            if str(key).casefold() not in _SENSITIVE_NESTED_KEYS
        }
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, (bool, int, float)) or value is None:
        return value
    return redact_sensitive_text(str(value))


def _stream_error(stream: QuarantinedNegotiationStream) -> str | None:
    error_reader = getattr(stream, "err", None)
    if not callable(error_reader):
        return None
    error = error_reader()
    return redact_sensitive_text(str(error)) if error is not None else None


def _task_error(task: asyncio.Task[None]) -> str | None:
    if task.cancelled():
        return "stream_cancelled"
    error = task.exception()
    return redact_sensitive_text(str(error)) if error is not None else None
