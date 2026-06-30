from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Literal

from pydantic import BaseModel, Field

from src.aegis_croo.cap.config import ControlledProviderRuntimeConfig
from src.aegis_croo.cap.controlled_provider_runtime import (
    ControlledProviderRuntime,
    RuntimeAction,
    SanitizedRuntimeEvent,
)
from src.aegis_croo.cap.pilot_readiness import (
    PilotReadinessRequest,
    PilotReadinessResult,
    PilotRunIDLookup,
    evaluate_pilot_readiness,
)
from src.aegis_croo.cap.ws_safety import redact_sensitive_text


OptionBPilotRunnerStatus = Literal[
    "no_go",
    "manual_review_plan_ready",
    "manual_review_simulated",
    "separate_approval_required",
    "simulation_error",
]


class OptionBNegotiationPilotRequest(BaseModel):
    readiness: PilotReadinessRequest = Field(
        default_factory=PilotReadinessRequest
    )
    connector_start_authorized: bool = False
    requester_kill_switch_enabled: bool = False


class ManualReviewConnectionPlan(BaseModel):
    option: Literal["option_b"] = "option_b"
    run_id: str
    directive: Literal["manual_review_only"] = "manual_review_only"
    runtime_timeout_seconds: float
    close_timeout_seconds: float
    max_events: Literal[1] = 1
    connection_attempted: Literal[False] = False
    provider_listener_started: Literal[False] = False
    live_execution_authorized: Literal[False] = False
    mutating_methods_called: Literal[False] = False
    real_cap_ready: Literal[False] = False


class OptionBNegotiationPilotResult(BaseModel):
    status: OptionBPilotRunnerStatus
    approval_ready: bool
    reason_codes: list[str] = Field(default_factory=list)
    connection_plan: ManualReviewConnectionPlan | None = None
    simulated_event: SanitizedRuntimeEvent | None = None
    directive_action: RuntimeAction | None = None
    runtime_status: str | None = None
    closed: bool = False
    local_only: Literal[True] = True
    manual_review_only: Literal[True] = True
    connection_attempted: Literal[False] = False
    provider_listener_started: Literal[False] = False
    live_execution_authorized: Literal[False] = False
    mutating_methods_called: Literal[False] = False
    real_cap_ready: Literal[False] = False
    error: str | None = None


class OptionBNegotiationPilotRunner:
    """Prepare and fake-test Option B without exposing a live connector."""

    def prepare(
        self,
        request: OptionBNegotiationPilotRequest,
        *,
        run_registry: PilotRunIDLookup | None = None,
    ) -> OptionBNegotiationPilotResult:
        readiness = evaluate_pilot_readiness(
            request.readiness,
            run_registry=run_registry,
        )
        if readiness.status == "separate_approval_required":
            return _result_from_readiness(
                readiness,
                status="separate_approval_required",
            )

        reasons = list(readiness.reason_codes)
        if not request.connector_start_authorized:
            reasons.append("connector_start_not_authorized")
        if not request.requester_kill_switch_enabled:
            reasons.append("requester_kill_switch_disabled")
        reasons = list(dict.fromkeys(reasons))
        if readiness.status != "approval_ready" or reasons:
            return OptionBNegotiationPilotResult(
                status="no_go",
                approval_ready=False,
                reason_codes=reasons,
            )

        gates = request.readiness.gates
        run_id = request.readiness.run_id
        if run_id is None:
            return OptionBNegotiationPilotResult(
                status="no_go",
                approval_ready=False,
                reason_codes=["missing_run_id"],
            )
        return OptionBNegotiationPilotResult(
            status="manual_review_plan_ready",
            approval_ready=True,
            connection_plan=ManualReviewConnectionPlan(
                run_id=run_id,
                runtime_timeout_seconds=float(gates.runtime_timeout_seconds),
                close_timeout_seconds=float(gates.close_timeout_seconds),
            ),
        )

    async def simulate_negotiation(
        self,
        request: OptionBNegotiationPilotRequest,
        *,
        event: Mapping[str, Any],
        run_registry: PilotRunIDLookup | None = None,
    ) -> OptionBNegotiationPilotResult:
        prepared = self.prepare(request, run_registry=run_registry)
        if prepared.status != "manual_review_plan_ready":
            return prepared

        if event.get("type") != "order_negotiation_created":
            return OptionBNegotiationPilotResult(
                status="no_go",
                approval_ready=False,
                reason_codes=["unsupported_event_type"],
            )

        plan = prepared.connection_plan
        if plan is None:
            return OptionBNegotiationPilotResult(
                status="simulation_error",
                approval_ready=False,
                reason_codes=["missing_connection_plan"],
            )

        stream = _SyntheticNegotiationStream(dict(event))
        runtime = ControlledProviderRuntime(
            config=ControlledProviderRuntimeConfig(
                runtime_enabled=True,
                accept_enabled=False,
                reject_enabled=False,
                paid_order_handling_enabled=False,
                deliver_enabled=False,
                timeout_seconds=plan.runtime_timeout_seconds,
                close_timeout_seconds=plan.close_timeout_seconds,
                max_events=1,
            )
        )
        runtime_result = await runtime.run(stream, stream.emit_once)
        directive = (
            runtime_result.directives[0]
            if len(runtime_result.directives) == 1
            else None
        )
        if directive is None or directive.action != "would_manual_review":
            return OptionBNegotiationPilotResult(
                status="simulation_error",
                approval_ready=False,
                reason_codes=["manual_review_invariant_failed"],
                connection_plan=plan,
                runtime_status=runtime_result.status,
                closed=runtime_result.closed,
                error=redact_sensitive_text(runtime_result.error or ""),
            )

        return OptionBNegotiationPilotResult(
            status="manual_review_simulated",
            approval_ready=True,
            reason_codes=list(directive.reason_codes),
            connection_plan=plan,
            simulated_event=directive.event,
            directive_action=directive.action,
            runtime_status=runtime_result.status,
            closed=runtime_result.closed,
            error=(
                redact_sensitive_text(runtime_result.error)
                if runtime_result.error
                else None
            ),
        )


class _SyntheticNegotiationStream:
    """Single-event memory stream used only by explicit fake simulation."""

    def __init__(self, event: dict[str, Any]) -> None:
        self._event = event
        self._handler: Callable[[Any], None] | None = None

    def on_any(self, handler: Callable[[Any], None]) -> None:
        self._handler = handler

    async def emit_once(self, _stream: Any) -> None:
        if self._handler is None:
            raise RuntimeError("Synthetic event handler is not registered.")
        self._handler(self._event)

    async def close(self) -> None:
        self._event = {}
        self._handler = None


def _result_from_readiness(
    readiness: PilotReadinessResult,
    *,
    status: OptionBPilotRunnerStatus,
) -> OptionBNegotiationPilotResult:
    return OptionBNegotiationPilotResult(
        status=status,
        approval_ready=False,
        reason_codes=list(readiness.reason_codes),
    )
