from __future__ import annotations

from typing import Literal, Protocol

from pydantic import BaseModel, Field

from src.aegis_croo.cap.controlled_provider_runtime import (
    ControlledProviderRuntime,
    ControlledProviderRuntimeResult,
    ControlledProviderStream,
)
from src.aegis_croo.cap.pilot_readiness import (
    PilotReadinessRequest,
    PilotReadinessResult,
    PilotRunIDLookup,
    evaluate_pilot_readiness,
)
from src.aegis_croo.cap.ws_safety import bounded_close, redact_sensitive_text


LiveConnectorWrapperStatus = Literal[
    "no_go",
    "approval_ready_not_started",
    "separate_approval_required",
    "runtime_completed",
    "runtime_error",
    "close_failed",
    "setup_failed",
]


class FutureProviderConnector(Protocol):
    async def open_stream(self) -> ControlledProviderStream: ...

    async def connect(self, stream: ControlledProviderStream) -> None: ...


class LiveConnectorWrapperRequest(BaseModel):
    readiness: PilotReadinessRequest = Field(
        default_factory=PilotReadinessRequest
    )
    connector_start_authorized: bool = False


class LiveConnectorWrapperResult(BaseModel):
    status: LiveConnectorWrapperStatus
    option: Literal["option_b", "option_c"]
    readiness_status: Literal[
        "no_go",
        "approval_ready",
        "separate_approval_required",
    ]
    approval_ready: bool
    reason_codes: list[str] = Field(default_factory=list)
    local_only: Literal[True] = True
    real_action_performed: Literal[False] = False
    live_execution_authorized: Literal[False] = False
    real_cap_ready: Literal[False] = False
    connector_started: bool
    close_attempted: bool
    closed: bool
    runtime_result: ControlledProviderRuntimeResult | None = None
    error: str | None = None


class LiveConnectorWrapper:
    """Guard future provider connection behind local readiness and fakes."""

    def __init__(
        self,
        *,
        connector: FutureProviderConnector,
        runtime: ControlledProviderRuntime,
    ) -> None:
        self._connector = connector
        self._runtime = runtime

    async def run(
        self,
        request: LiveConnectorWrapperRequest,
        *,
        run_registry: PilotRunIDLookup | None = None,
    ) -> LiveConnectorWrapperResult:
        readiness = evaluate_pilot_readiness(
            request.readiness,
            run_registry=run_registry,
        )
        if readiness.status != "approval_ready":
            return _not_started_result(readiness, status=readiness.status)
        if readiness.option != "option_b":
            return _not_started_result(
                readiness,
                status="separate_approval_required",
            )
        if not request.connector_start_authorized:
            return _not_started_result(
                readiness,
                status="approval_ready_not_started",
            )

        stream: ControlledProviderStream | None = None
        try:
            stream = await self._connector.open_stream()
            runtime_result = await self._runtime.run(
                stream,
                self._connector.connect,
            )
        except Exception as exc:
            closed = False
            close_attempted = False
            close_error: str | None = None
            if stream is not None:
                close_attempted = True
                closed, close_error = await bounded_close(
                    stream,
                    timeout_seconds=_safe_close_timeout_seconds(request),
                )
            error = close_error or redact_sensitive_text(str(exc))
            return LiveConnectorWrapperResult(
                status="setup_failed",
                option=readiness.option,
                readiness_status=readiness.status,
                approval_ready=readiness.approval_ready,
                reason_codes=readiness.reason_codes,
                connector_started=False,
                close_attempted=close_attempted,
                closed=closed,
                error=error,
            )

        status: LiveConnectorWrapperStatus
        if runtime_result.status == "close_failed":
            status = "close_failed"
        elif runtime_result.status == "completed":
            status = "runtime_completed"
        else:
            status = "runtime_error"
        return LiveConnectorWrapperResult(
            status=status,
            option=readiness.option,
            readiness_status=readiness.status,
            approval_ready=readiness.approval_ready,
            reason_codes=readiness.reason_codes,
            connector_started=True,
            close_attempted=runtime_result.close_attempted,
            closed=runtime_result.closed,
            runtime_result=runtime_result,
            error=runtime_result.error,
        )


def _not_started_result(
    readiness: PilotReadinessResult,
    *,
    status: LiveConnectorWrapperStatus,
) -> LiveConnectorWrapperResult:
    return LiveConnectorWrapperResult(
        status=status,
        option=readiness.option,
        readiness_status=readiness.status,
        approval_ready=readiness.approval_ready,
        reason_codes=readiness.reason_codes,
        connector_started=False,
        close_attempted=False,
        closed=False,
    )


def _safe_close_timeout_seconds(
    request: LiveConnectorWrapperRequest,
) -> float:
    value = request.readiness.gates.close_timeout_seconds
    return value if value is not None and 0 < value <= 1.0 else 1.0
