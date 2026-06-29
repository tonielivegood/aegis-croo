from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from src.aegis_croo.cap.config import configured_real_provider_enabled
from src.aegis_croo.cap.provider_guard import (
    CAPProviderGuardResult,
    GuardDecision,
    evaluate_cap_provider_guard,
)


ProviderPlannedAction = Literal[
    "would_accept",
    "would_reject",
    "would_manual_review",
    "would_deliver_after_paid",
]

LOCAL_PROVIDER_ADAPTER_DISCLAIMER = (
    "Local disabled-by-default provider adapter skeleton only. This plan does not "
    "connect to CROO, accept or reject an order, transfer funds, deliver output, "
    "upload files, settle CAP, or make Aegis online."
)


class CAPProviderActionPlan(BaseModel):
    provider_enabled: Literal[True] = True
    local_only: Literal[True] = True
    real_action_performed: Literal[False] = False
    real_cap_ready: Literal[False] = False
    guard_decision: GuardDecision
    planned_actions: list[ProviderPlannedAction] = Field(min_length=1)
    reason_codes: list[str] = Field(default_factory=list)
    disclaimer: str = LOCAL_PROVIDER_ADAPTER_DISCLAIMER


class CAPProviderAdapterDisabledError(RuntimeError):
    pass


class CAPProviderAdapterSkeleton:
    """Plan hypothetical provider actions locally; never perform provider actions."""

    def __init__(self, *, enabled: bool) -> None:
        if not enabled:
            raise CAPProviderAdapterDisabledError(
                "CAP provider adapter skeleton is disabled. "
                "Set CAP_REAL_PROVIDER_ENABLED=true only for local planning tests."
            )

    @classmethod
    def from_environment(cls) -> "CAPProviderAdapterSkeleton":
        return cls(enabled=configured_real_provider_enabled())

    def plan(self, payload: dict[str, Any]) -> CAPProviderActionPlan:
        guard_result = evaluate_cap_provider_guard(payload)
        return _plan_from_guard_result(guard_result)


def _plan_from_guard_result(
    guard_result: CAPProviderGuardResult,
) -> CAPProviderActionPlan:
    actions_by_decision: dict[GuardDecision, list[ProviderPlannedAction]] = {
        "accept_candidate": ["would_accept", "would_deliver_after_paid"],
        "reject": ["would_reject"],
        "manual_review": ["would_manual_review"],
    }
    return CAPProviderActionPlan(
        guard_decision=guard_result.decision,
        planned_actions=actions_by_decision[guard_result.decision],
        reason_codes=guard_result.reason_codes,
    )
