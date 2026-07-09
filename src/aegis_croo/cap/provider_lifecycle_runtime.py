from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal, Protocol
from uuid import uuid4

from pydantic import BaseModel, Field, ValidationError

from src.aegis_croo.cap.config import LifecycleCanaryConfig
from src.aegis_croo.cap.delivery_mapping import build_cap_delivery_mapping
from src.aegis_croo.cap.provider_guard import (
    AEGIS_CAP_SERVICE_ID,
    AEGIS_CAP_SERVICE_NAME,
    CAPProviderGuardResult,
    evaluate_cap_provider_guard,
)
from src.aegis_croo.cap.ws_safety import redact_sensitive_text
from src.aegis_croo.oracle.risk_oracle import assess_risk
from src.aegis_croo.orders.proof import build_delivery_proof
from src.aegis_croo.schemas.risk import RiskCheckRequest, RiskCheckResponse


# Exact installed croo-sdk 0.2.1 event type values (types.py EventType). Kept
# as local literals so this module never imports croo at module level.
EVENT_NEGOTIATION_CREATED = "order_negotiation_created"
EVENT_ORDER_PAID = "order_paid"

GuardEvaluator = Callable[[dict[str, Any]], CAPProviderGuardResult]
RiskAssessor = Callable[[RiskCheckRequest], RiskCheckResponse]


class LifecycleStream(Protocol):
    def on(self, event_type: str, handler: Callable[[Any], None]) -> None: ...

    async def close(self) -> None: ...


class LifecycleClient(Protocol):
    async def connect_websocket(self) -> LifecycleStream: ...

    async def get_negotiation(self, negotiation_id: str) -> Any: ...

    async def accept_negotiation(self, negotiation_id: str) -> Any: ...

    async def get_order(self, order_id: str) -> Any: ...

    async def deliver_order(
        self,
        order_id: str,
        *,
        deliverable_type: str,
        deliverable_schema: str,
        deliverable_text: str,
    ) -> Any: ...

    async def close(self) -> None: ...


class NegotiationOutcome(BaseModel):
    status: Literal["accepted", "rejected_locally"]
    negotiation_id: str
    reason_code: str | None = None
    detail_reason_codes: list[str] = Field(default_factory=list)
    error: str | None = None


class OrderOutcome(BaseModel):
    status: Literal["delivered", "stopped_locally"]
    order_id: str
    reason_code: str | None = None
    proof_id: str | None = None
    decision: str | None = None
    error: str | None = None


@dataclass
class SingleOrderCanaryState:
    """In-memory, exactly-once tracking for one canary run.

    This is deliberately not durable: it resets on process restart. That is
    acceptable only because this runtime is hard-capped to a single accepted
    negotiation and a single delivered order (see config.LIFECYCLE_CANARY_MAX_*),
    never a production queue.
    """

    processed_negotiation_ids: set[str] = field(default_factory=set)
    processed_order_ids: set[str] = field(default_factory=set)
    accepted_negotiation_id: str | None = None
    stored_requirements: RiskCheckRequest | None = None
    delivered_order_id: str | None = None


class ProviderLifecycleRuntime:
    """Narrow, gated, single-order real CAP lifecycle wiring.

    Registers no handler beyond NEGOTIATION_CREATED/ORDER_PAID. Never calls
    reject_negotiation, reject_order, accept_negotiation_with_fund_address, or
    upload_file. Every mutating call (accept_negotiation, deliver_order) is
    reachable only if the top-level lifecycle gate, the specific per-action
    gate, the service/requester allowlist, and the one-order budget all pass.
    """

    def __init__(
        self,
        *,
        client: LifecycleClient,
        gates: LifecycleCanaryConfig,
        guard_evaluator: GuardEvaluator = evaluate_cap_provider_guard,
        risk_assessor: RiskAssessor = assess_risk,
        state: SingleOrderCanaryState | None = None,
    ) -> None:
        self._client = client
        self._gates = gates
        self._guard_evaluator = guard_evaluator
        self._risk_assessor = risk_assessor
        self._state = state or SingleOrderCanaryState()
        self._tasks: list[asyncio.Task[Any]] = []

    def register_handlers(self, stream: LifecycleStream) -> None:
        """Register synchronous SDK callbacks that schedule the async handlers.

        The installed SDK dispatches event handlers synchronously; real async
        work is scheduled via asyncio.create_task from within the callback,
        matching the official provider example's own pattern.
        """
        stream.on(EVENT_NEGOTIATION_CREATED, self._on_negotiation_created)
        stream.on(EVENT_ORDER_PAID, self._on_order_paid)

    def _on_negotiation_created(self, event: Any) -> None:
        self._tasks.append(
            asyncio.create_task(self.handle_negotiation_created(event))
        )

    def _on_order_paid(self, event: Any) -> None:
        self._tasks.append(asyncio.create_task(self.handle_order_paid(event)))

    async def handle_negotiation_created(self, event: Any) -> NegotiationOutcome:
        negotiation_id = str(getattr(event, "negotiation_id", "") or "")
        if not negotiation_id:
            return self._reject(reason_code="missing_negotiation_id", negotiation_id="")

        if negotiation_id in self._state.processed_negotiation_ids:
            return self._reject(
                reason_code="duplicate_negotiation_event",
                negotiation_id=negotiation_id,
            )
        self._state.processed_negotiation_ids.add(negotiation_id)

        if not self._gates.lifecycle_enabled or not self._gates.accept_enabled:
            return self._reject(
                reason_code="lifecycle_or_accept_gate_disabled",
                negotiation_id=negotiation_id,
            )

        if self._state.accepted_negotiation_id is not None:
            return self._reject(
                reason_code="single_negotiation_budget_consumed",
                negotiation_id=negotiation_id,
            )

        if self._gates.missing_allowlist:
            return self._reject(
                reason_code="allowlist_not_configured", negotiation_id=negotiation_id
            )

        try:
            negotiation = await self._client.get_negotiation(negotiation_id)
        except Exception as exc:  # noqa: BLE001
            return self._reject(
                reason_code="get_negotiation_failed",
                negotiation_id=negotiation_id,
                error=redact_sensitive_text(str(exc)),
            )

        service_id = str(getattr(negotiation, "service_id", "") or "")
        requester_agent_id = str(getattr(negotiation, "requester_agent_id", "") or "")
        requirements_raw = getattr(negotiation, "requirements", "") or ""
        fund_amount = str(getattr(negotiation, "fund_amount", "") or "")
        fund_token = str(getattr(negotiation, "fund_token", "") or "")

        if service_id != self._gates.expected_service_id:
            return self._reject(
                reason_code="service_id_mismatch", negotiation_id=negotiation_id
            )
        if requester_agent_id != self._gates.expected_requester_agent_id:
            return self._reject(
                reason_code="requester_agent_id_mismatch",
                negotiation_id=negotiation_id,
            )

        try:
            requirements_payload = json.loads(requirements_raw) if requirements_raw else None
        except (TypeError, ValueError):
            return self._reject(
                reason_code="requirements_not_valid_json",
                negotiation_id=negotiation_id,
            )
        if not isinstance(requirements_payload, dict):
            return self._reject(
                reason_code="requirements_not_object", negotiation_id=negotiation_id
            )

        # The real negotiation's service_id/requester_agent_id were already
        # verified above against our own allowlist (config.expected_*), which
        # holds the real CROO-issued values. evaluate_cap_provider_guard uses
        # its own separate local placeholder service_id/service_name
        # constants (see provider_guard.AEGIS_CAP_SERVICE_ID) that predate
        # owner-verified Dashboard evidence and must not be edited here — see
        # docs/step7d-b-real-cap-pilot-runbook-2026-06-30.md. Supplying the
        # guard's own expected identity constants lets us reuse its
        # requirements-schema, fund-transfer, and forbidden-execution checks
        # without re-implementing them or weakening the guard's existing tests.
        guard_result = self._guard_evaluator(
            {
                "service_id": AEGIS_CAP_SERVICE_ID,
                "service_name": AEGIS_CAP_SERVICE_NAME,
                "requirements_type": "schema",
                "requirements": requirements_payload,
                "requires_fund_transfer": bool(fund_amount or fund_token),
            }
        )
        if guard_result.decision != "accept_candidate":
            return self._reject(
                reason_code="guard_rejected",
                negotiation_id=negotiation_id,
                reason_codes=guard_result.reason_codes,
            )

        try:
            risk_request = RiskCheckRequest.model_validate(requirements_payload)
        except ValidationError:
            return self._reject(
                reason_code="risk_request_invalid", negotiation_id=negotiation_id
            )

        try:
            await self._client.accept_negotiation(negotiation_id)
        except Exception as exc:  # noqa: BLE001
            return self._reject(
                reason_code="accept_negotiation_call_failed",
                negotiation_id=negotiation_id,
                error=redact_sensitive_text(str(exc)),
            )

        self._state.accepted_negotiation_id = negotiation_id
        self._state.stored_requirements = risk_request
        return NegotiationOutcome(status="accepted", negotiation_id=negotiation_id)

    async def handle_order_paid(self, event: Any) -> OrderOutcome:
        order_id = str(getattr(event, "order_id", "") or "")
        if not order_id:
            return self._stop(reason_code="missing_order_id", order_id="")

        if order_id in self._state.processed_order_ids:
            return self._stop(reason_code="duplicate_order_event", order_id=order_id)
        self._state.processed_order_ids.add(order_id)

        if not self._gates.lifecycle_enabled or not self._gates.deliver_enabled:
            return self._stop(
                reason_code="lifecycle_or_deliver_gate_disabled", order_id=order_id
            )

        if self._state.delivered_order_id is not None:
            return self._stop(
                reason_code="single_order_budget_consumed", order_id=order_id
            )

        if (
            self._state.accepted_negotiation_id is None
            or self._state.stored_requirements is None
        ):
            return self._stop(
                reason_code="no_accepted_negotiation_on_record", order_id=order_id
            )

        try:
            order = await self._client.get_order(order_id)
        except Exception as exc:  # noqa: BLE001
            return self._stop(
                reason_code="get_order_failed",
                order_id=order_id,
                error=redact_sensitive_text(str(exc)),
            )

        service_id = str(getattr(order, "service_id", "") or "")
        requester_agent_id = str(getattr(order, "requester_agent_id", "") or "")
        negotiation_id = str(getattr(order, "negotiation_id", "") or "")
        status = str(getattr(order, "status", "") or "")

        if service_id != self._gates.expected_service_id:
            return self._stop(reason_code="service_id_mismatch", order_id=order_id)
        if requester_agent_id != self._gates.expected_requester_agent_id:
            return self._stop(
                reason_code="requester_agent_id_mismatch", order_id=order_id
            )
        if negotiation_id != self._state.accepted_negotiation_id:
            return self._stop(
                reason_code="order_not_from_accepted_negotiation", order_id=order_id
            )
        if status and status != "paid":
            return self._stop(reason_code="order_status_not_paid", order_id=order_id)

        risk_request = self._state.stored_requirements
        risk_response = self._risk_assessor(risk_request)

        proof_id = f"proof_{uuid4().hex}"
        proof = build_delivery_proof(
            proof_id=proof_id,
            order_id=order_id,
            request_payload=risk_request.model_dump(mode="json"),
            risk_response=risk_response,
            created_at=datetime.now(UTC),
        )
        mapping = build_cap_delivery_mapping(risk_response=risk_response, proof=proof)

        try:
            await self._client.deliver_order(
                order_id,
                deliverable_type=mapping.deliverable_type,
                deliverable_schema=mapping.deliverable_schema,
                deliverable_text=mapping.deliverable_text,
            )
        except Exception as exc:  # noqa: BLE001
            return self._stop(
                reason_code="deliver_order_call_failed",
                order_id=order_id,
                error=redact_sensitive_text(str(exc)),
            )

        self._state.delivered_order_id = order_id
        return OrderOutcome(
            status="delivered",
            order_id=order_id,
            proof_id=proof_id,
            decision=risk_response.decision.value,
        )

    def _reject(
        self,
        *,
        reason_code: str,
        negotiation_id: str,
        reason_codes: list[str] | None = None,
        error: str | None = None,
    ) -> NegotiationOutcome:
        return NegotiationOutcome(
            status="rejected_locally",
            negotiation_id=negotiation_id,
            reason_code=reason_code,
            detail_reason_codes=list(reason_codes or []),
            error=error,
        )

    def _stop(
        self,
        *,
        reason_code: str,
        order_id: str,
        error: str | None = None,
    ) -> OrderOutcome:
        return OrderOutcome(
            status="stopped_locally",
            order_id=order_id,
            reason_code=reason_code,
            error=error,
        )
