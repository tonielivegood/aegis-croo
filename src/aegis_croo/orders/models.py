from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

from src.aegis_croo.schemas.common import Confidence, Decision
from src.aegis_croo.schemas.risk import RiskCheckRequest, RiskFactor


CAP_DISCLAIMER = (
    "Local mock ledger only. No real CAP payment, escrow, on-chain delivery, "
    "or settlement."
)


class OrderLifecycleStatus(StrEnum):
    NEGOTIATED_MOCK = "NEGOTIATED_MOCK"
    LOCKED_MOCK = "LOCKED_MOCK"
    DELIVERED = "DELIVERED"
    CLEARED_MOCK = "CLEARED_MOCK"


class LocalOrderRequest(BaseModel):
    requester_agent_id: str = Field(min_length=1)
    provider_agent_id: str = Field(min_length=1)
    service_id: str = Field(min_length=1)
    service_name: str = Field(min_length=1)
    sla_minutes: int = Field(gt=0)
    price_usdc: float = Field(ge=0)
    requirements_type: Literal["schema", "text"]
    deliverable_type: Literal["schema", "text"]
    request: RiskCheckRequest


class LocalDeliveryProof(BaseModel):
    proof_id: str = Field(min_length=1)
    order_id: str = Field(min_length=1)
    request_hash: str = Field(min_length=64, max_length=64)
    response_hash: str = Field(min_length=64, max_length=64)
    result_hash: str = Field(min_length=64, max_length=64)
    policy_version: str = Field(min_length=1)
    deliverable_type: Literal["schema"]
    created_at: datetime


class LocalOrderResult(BaseModel):
    order_id: str = Field(min_length=1)
    requester_agent_id: str = Field(min_length=1)
    provider_agent_id: str = Field(min_length=1)
    service_id: str = Field(min_length=1)
    service_name: str = Field(min_length=1)
    status: OrderLifecycleStatus
    lifecycle: list[OrderLifecycleStatus]
    price_usdc: float = Field(ge=0)
    sla_minutes: int = Field(gt=0)
    requirements_type: Literal["schema", "text"]
    deliverable_type: Literal["schema", "text"]
    decision: Decision
    risk_score: int = Field(ge=0, le=100)
    confidence: Confidence
    safe_to_execute: bool
    risk_factors: list[RiskFactor]
    reasons: list[str]
    suggested_action: str
    proof_id: str = Field(min_length=1)
    proof: LocalDeliveryProof
    created_at: datetime
    completed_at: datetime
    cap_mode: Literal["local_mock"] = "local_mock"
    cap_disclaimer: str = CAP_DISCLAIMER
