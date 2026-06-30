from __future__ import annotations

import re
from decimal import Decimal
from threading import RLock
from typing import Literal, Protocol

from pydantic import BaseModel, Field


PilotOption = Literal["option_b", "option_c"]
PilotReadinessStatus = Literal[
    "no_go",
    "approval_ready",
    "separate_approval_required",
]
WouldAction = Literal[
    "would_receive_negotiation",
    "would_manual_review",
    "would_accept",
    "would_pay",
    "would_deliver_schema",
    "would_close",
]

EXPECTED_SERVICE_PRICE_USDC = Decimal("0.12")
_RUN_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")


class SanitizedDashboardStatus(BaseModel):
    profile_complete: bool | None = None
    service_identity_verified: bool | None = None
    service_price_usdc: Decimal | None = None
    require_fund_transfer: bool | None = None
    requirements_schema_verified: bool | None = None
    deliverable_schema_verified: bool | None = None
    no_pending_negotiations_or_orders: bool | None = None


class PilotGateSnapshot(BaseModel):
    cap_mode: Literal["mock", "real"] | None = None
    real_provider_enabled: bool | None = None
    controlled_runtime_enabled: bool | None = None
    observe_only_enabled: bool | None = None
    requester_enabled: bool | None = None
    negotiate_enabled: bool | None = None
    pay_enabled: bool | None = None
    accept_enabled: bool | None = None
    reject_enabled: bool | None = None
    paid_order_handling_enabled: bool | None = None
    deliver_enabled: bool | None = None
    no_retry: bool | None = None
    runtime_timeout_seconds: float | None = None
    close_timeout_seconds: float | None = None
    max_events: int | None = None


class PilotReadinessRequest(BaseModel):
    option: PilotOption = "option_b"
    git_status_clean: bool | None = None
    dashboard: SanitizedDashboardStatus = Field(
        default_factory=SanitizedDashboardStatus
    )
    gates: PilotGateSnapshot = Field(default_factory=PilotGateSnapshot)
    run_id: str | None = None
    approval_granted: bool | None = None
    approval_token_present: bool | None = None
    option_c_future_step_enabled: Literal[False] = False


class PilotReadinessResult(BaseModel):
    status: PilotReadinessStatus
    option: PilotOption
    approval_ready: bool
    local_only: Literal[True] = True
    real_action_performed: Literal[False] = False
    live_execution_authorized: Literal[False] = False
    real_cap_ready: Literal[False] = False
    reason_codes: list[str] = Field(default_factory=list)


class SanitizedPilotEvidence(BaseModel):
    run_id: str = Field(min_length=1, max_length=64)
    option: PilotOption
    readiness_status: PilotReadinessStatus
    reason_codes: list[str] = Field(default_factory=list)


class PilotRunLock(BaseModel):
    run_id: str
    option: PilotOption
    approval_granted: Literal[True] = True
    approval_token_present: Literal[True] = True
    evidence: SanitizedPilotEvidence


class PilotActionDirective(BaseModel):
    action: WouldAction
    reason_codes: list[str] = Field(default_factory=list)
    local_only: Literal[True] = True
    real_action_performed: Literal[False] = False


class PilotRunIDLookup(Protocol):
    def contains(self, run_id: str) -> bool: ...


class PilotActionAdapter(Protocol):
    def record(
        self,
        action: WouldAction,
        reason_codes: list[str] | None = None,
    ) -> PilotActionDirective: ...

    def directives(self) -> list[PilotActionDirective]: ...


class DuplicatePilotRunIDError(RuntimeError):
    pass


class PilotApprovalRequiredError(RuntimeError):
    pass


class PilotRunLockRegistry:
    """Process-local future-pilot run locks containing sanitized evidence only."""

    def __init__(self) -> None:
        self._locks: dict[str, PilotRunLock] = {}
        self._lock = RLock()

    def contains(self, run_id: str) -> bool:
        with self._lock:
            return run_id in self._locks

    def get(self, run_id: str) -> PilotRunLock | None:
        with self._lock:
            lock = self._locks.get(run_id)
            return lock.model_copy(deep=True) if lock is not None else None

    def reserve(
        self,
        *,
        run_id: str,
        option: PilotOption,
        approval_granted: bool,
        approval_token_present: bool,
        evidence: SanitizedPilotEvidence,
    ) -> PilotRunLock:
        if not approval_granted or not approval_token_present:
            raise PilotApprovalRequiredError(
                "Explicit pilot approval and token-presence evidence are required."
            )
        if not _valid_run_id(run_id):
            raise ValueError("Pilot run ID must be a sanitized nonsecret identifier.")
        if evidence.run_id != run_id or evidence.option != option:
            raise ValueError("Pilot evidence must match the run lock identity.")
        with self._lock:
            if run_id in self._locks:
                raise DuplicatePilotRunIDError(
                    "Pilot run ID has already been reserved."
                )
            lock = PilotRunLock(
                run_id=run_id,
                option=option,
                evidence=evidence,
            )
            self._locks[run_id] = lock
            return lock.model_copy(deep=True)


class FakePilotActionAdapter:
    """Record hypothetical directives; expose no real CAP action methods."""

    def __init__(self) -> None:
        self._items: list[PilotActionDirective] = []
        self._lock = RLock()

    def record(
        self,
        action: WouldAction,
        reason_codes: list[str] | None = None,
    ) -> PilotActionDirective:
        directive = PilotActionDirective(
            action=action,
            reason_codes=list(reason_codes or []),
        )
        with self._lock:
            self._items.append(directive)
        return directive.model_copy(deep=True)

    def directives(self) -> list[PilotActionDirective]:
        with self._lock:
            return [item.model_copy(deep=True) for item in self._items]


def evaluate_pilot_readiness(
    request: PilotReadinessRequest,
    *,
    run_registry: PilotRunIDLookup | None = None,
) -> PilotReadinessResult:
    """Evaluate injected, sanitized facts without shell, SDK, or network access."""
    reasons: list[str] = []
    dashboard = request.dashboard
    gates = request.gates

    if request.git_status_clean is not True:
        reasons.append("git_status_not_clean")

    dashboard_checks = (
        dashboard.profile_complete,
        dashboard.service_identity_verified,
        dashboard.requirements_schema_verified,
        dashboard.deliverable_schema_verified,
    )
    if any(value is not True for value in dashboard_checks):
        reasons.append("dashboard_check_failed")
    if dashboard.service_price_usdc != EXPECTED_SERVICE_PRICE_USDC:
        reasons.append("wrong_service_price")
    if dashboard.require_fund_transfer is not False:
        reasons.append("fund_transfer_enabled")
    if dashboard.no_pending_negotiations_or_orders is not True:
        reasons.append("pending_negotiations_or_orders")

    if not request.run_id:
        reasons.append("missing_run_id")
    elif not _valid_run_id(request.run_id):
        reasons.append("invalid_run_id")
    elif run_registry is not None and run_registry.contains(request.run_id):
        reasons.append("duplicate_run_id")

    if request.approval_granted is not True:
        reasons.append("approval_not_granted")
    if request.approval_token_present is not True:
        reasons.append("approval_token_missing")

    required_gate_values = (
        gates.cap_mode,
        gates.real_provider_enabled,
        gates.controlled_runtime_enabled,
        gates.observe_only_enabled,
        gates.requester_enabled,
        gates.negotiate_enabled,
        gates.pay_enabled,
        gates.accept_enabled,
        gates.reject_enabled,
        gates.paid_order_handling_enabled,
        gates.deliver_enabled,
        gates.no_retry,
        gates.runtime_timeout_seconds,
        gates.close_timeout_seconds,
        gates.max_events,
    )
    if any(value is None for value in required_gate_values):
        reasons.append("required_gate_not_explicit")

    if gates.cap_mode != "real":
        reasons.append("real_mode_not_requested")
    if gates.real_provider_enabled is not True:
        reasons.append("real_provider_gate_disabled")
    if gates.controlled_runtime_enabled is not True:
        reasons.append("controlled_runtime_gate_disabled")
    if gates.observe_only_enabled is not False:
        reasons.append("observe_only_gate_must_remain_off")
    if gates.requester_enabled is not True:
        reasons.append("requester_gate_disabled")
    if gates.negotiate_enabled is not True:
        reasons.append("negotiate_gate_disabled")
    if gates.no_retry is not True:
        reasons.append("retry_not_disabled")

    if not _bounded(gates.runtime_timeout_seconds, maximum=5.0):
        reasons.append("runtime_timeout_unbounded")
    if not _bounded(gates.close_timeout_seconds, maximum=1.0):
        reasons.append("close_timeout_unbounded")

    if request.option == "option_b":
        if gates.max_events != 1:
            reasons.append("event_limit_invalid")
        if any(
            value is not False
            for value in (
                gates.pay_enabled,
                gates.accept_enabled,
                gates.reject_enabled,
                gates.paid_order_handling_enabled,
                gates.deliver_enabled,
            )
        ):
            reasons.append("option_b_mutation_gate_enabled")
    else:
        if gates.max_events != 3:
            reasons.append("event_limit_invalid")
        if not (
            gates.pay_enabled is True
            and gates.accept_enabled is True
            and gates.reject_enabled is False
            and gates.paid_order_handling_enabled is True
            and gates.deliver_enabled is True
        ):
            reasons.append("option_c_gate_mismatch")

    reasons = list(dict.fromkeys(reasons))
    if reasons:
        return PilotReadinessResult(
            status="no_go",
            option=request.option,
            approval_ready=False,
            reason_codes=reasons,
        )
    if request.option == "option_c":
        return PilotReadinessResult(
            status="separate_approval_required",
            option=request.option,
            approval_ready=False,
            reason_codes=["option_c_future_step_required"],
        )
    return PilotReadinessResult(
        status="approval_ready",
        option=request.option,
        approval_ready=True,
        reason_codes=[],
    )


def _valid_run_id(value: str) -> bool:
    return bool(_RUN_ID_PATTERN.fullmatch(value))


def _bounded(value: float | None, *, maximum: float) -> bool:
    return value is not None and 0 < value <= maximum
