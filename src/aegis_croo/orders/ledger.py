from collections.abc import Callable
from datetime import UTC, datetime
from threading import RLock
from uuid import uuid4

from src.aegis_croo.oracle.risk_oracle import assess_risk
from src.aegis_croo.orders.models import (
    LocalDeliveryProof,
    LocalOrderRequest,
    LocalOrderResult,
    OrderLifecycleStatus,
)
from src.aegis_croo.orders.proof import build_delivery_proof
from src.aegis_croo.schemas.risk import RiskCheckRequest, RiskCheckResponse


RiskAssessor = Callable[[RiskCheckRequest], RiskCheckResponse]

LOCAL_LIFECYCLE = [
    OrderLifecycleStatus.NEGOTIATED_MOCK,
    OrderLifecycleStatus.LOCKED_MOCK,
    OrderLifecycleStatus.DELIVERED,
    OrderLifecycleStatus.CLEARED_MOCK,
]


class InMemoryOrderLedger:
    def __init__(self, risk_assessor: RiskAssessor = assess_risk) -> None:
        self._risk_assessor = risk_assessor
        self._orders: dict[str, LocalOrderResult] = {}
        self._proofs: dict[str, LocalDeliveryProof] = {}
        self._lock = RLock()

    def create_order(self, request: LocalOrderRequest) -> LocalOrderResult:
        created_at = datetime.now(UTC)
        order_id = f"order_{uuid4().hex}"
        proof_id = f"proof_{uuid4().hex}"
        risk = self._risk_assessor(request.request)
        proof = build_delivery_proof(
            proof_id=proof_id,
            order_id=order_id,
            request_payload=request.model_dump(mode="json"),
            risk_response=risk,
            created_at=created_at,
        )
        completed_at = datetime.now(UTC)
        order = LocalOrderResult(
            order_id=order_id,
            requester_agent_id=request.requester_agent_id,
            provider_agent_id=request.provider_agent_id,
            service_id=request.service_id,
            service_name=request.service_name,
            status=OrderLifecycleStatus.CLEARED_MOCK,
            lifecycle=list(LOCAL_LIFECYCLE),
            price_usdc=request.price_usdc,
            sla_minutes=request.sla_minutes,
            requirements_type=request.requirements_type,
            deliverable_type=request.deliverable_type,
            decision=risk.decision,
            risk_score=risk.risk_score,
            confidence=risk.confidence,
            safe_to_execute=risk.safe_to_execute,
            risk_factors=risk.risk_factors,
            reasons=risk.reasons,
            suggested_action=risk.suggested_action,
            proof_id=proof_id,
            proof=proof,
            created_at=created_at,
            completed_at=completed_at,
        )
        with self._lock:
            self._orders[order_id] = order
            self._proofs[proof_id] = proof
        return order

    def get_order(self, order_id: str) -> LocalOrderResult | None:
        with self._lock:
            return self._orders.get(order_id)

    def get_proof(self, proof_id: str) -> LocalDeliveryProof | None:
        with self._lock:
            return self._proofs.get(proof_id)
