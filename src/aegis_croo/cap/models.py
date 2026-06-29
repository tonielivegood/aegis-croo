from typing import Literal

from pydantic import BaseModel, Field

from src.aegis_croo.orders.models import LocalDeliveryProof, LocalOrderRequest, LocalOrderResult


CAP_ADAPTER_STATUS = "CAP_READY_LOCAL_MOCK"
CAP_ADAPTER_DISCLAIMER = (
    "CAP adapter mock only. No real CROO SDK payment, escrow, settlement, "
    "reputation, or on-chain delivery."
)
MOCK_CAP_STATUS_DISCLAIMER = (
    "Mock CAP adapter only. No real CROO SDK payment, escrow, settlement, "
    "reputation, or on-chain delivery."
)
REAL_CAP_MISSING_DISCLAIMER = (
    "Real CAP mode requested, but credentials or service configuration are "
    "missing. No real CAP action was performed."
)
REAL_CAP_CONFIGURED_DISCLAIMER = (
    "Real CAP configuration is present, but Step 6 provider verification has "
    "not run. No real CAP action was performed."
)
REAL_CAP_CLIENT_INITIALIZED_REASON = (
    "SDK client initialized, but provider/service readiness requires official "
    "read-only verification or dashboard confirmation."
)
CAP_LIFECYCLE = ["NEGOTIATE_MOCK", "LOCK_MOCK", "DELIVER_LOCAL", "CLEAR_MOCK"]
REAL_CAP_PENDING_DETAIL = (
    "Real CROO/CAP integration is pending SDK credentials and Step 6 "
    "verification. This endpoint does not fake payment, escrow, settlement, "
    "reputation, or on-chain delivery."
)


class CAPOrderRequest(LocalOrderRequest):
    cap_mode: Literal["mock", "real"] | None = None


class CAPOrderResult(BaseModel):
    order_id: str = Field(min_length=1)
    requester_agent_id: str = Field(min_length=1)
    provider_agent_id: str = Field(min_length=1)
    service_id: str = Field(min_length=1)
    service_name: str = Field(min_length=1)
    status: str = Field(min_length=1)
    lifecycle: list[str]
    price_usdc: float = Field(ge=0)
    sla_minutes: int = Field(gt=0)
    requirements_type: Literal["schema", "text"]
    deliverable_type: Literal["schema", "text"]
    decision: str = Field(min_length=1)
    risk_score: int = Field(ge=0, le=100)
    confidence: str = Field(min_length=1)
    safe_to_execute: bool
    risk_factors: list[dict]
    reasons: list[str]
    suggested_action: str
    proof_id: str = Field(min_length=1)
    proof: LocalDeliveryProof
    created_at: str
    completed_at: str
    cap_mode: Literal["mock"] = "mock"
    cap_adapter_status: Literal["CAP_READY_LOCAL_MOCK"] = CAP_ADAPTER_STATUS
    cap_lifecycle: list[Literal[
        "NEGOTIATE_MOCK", "LOCK_MOCK", "DELIVER_LOCAL", "CLEAR_MOCK",
    ]] = Field(default_factory=lambda: list(CAP_LIFECYCLE))
    cap_disclaimer: str = CAP_ADAPTER_DISCLAIMER

    @classmethod
    def from_local_order(cls, local_order: LocalOrderResult) -> "CAPOrderResult":
        payload = local_order.model_dump(mode="json")
        payload["cap_mode"] = "mock"
        payload["cap_adapter_status"] = CAP_ADAPTER_STATUS
        payload["cap_lifecycle"] = list(CAP_LIFECYCLE)
        payload["cap_disclaimer"] = CAP_ADAPTER_DISCLAIMER
        return cls.model_validate(payload)


class CAPStatusResponse(BaseModel):
    cap_mode: Literal["mock", "real"]
    real_cap_ready: bool
    adapter_status: str = Field(min_length=1)
    sdk_import_status: str = Field(min_length=1)
    service_id_status: str = Field(min_length=1)
    credential_status: str = Field(min_length=1)
    provider_agent_id: str = Field(min_length=1)
    disclaimer: str = Field(min_length=1)
    client_init_status: str | None = None
    readiness_reason: str | None = None
    missing: list[str] | None = None
