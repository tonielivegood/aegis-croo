from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel

from src.aegis_croo.orders.models import LocalDeliveryProof
from src.aegis_croo.schemas.risk import RiskCheckResponse


class CAPDeliveryMapping(BaseModel):
    """Deterministic mapping of existing Aegis evidence into a CAP delivery payload.

    Field-shaped to match the installed SDK's ``DeliverOrderRequest``
    (``deliverable_type``, ``deliverable_schema``, ``deliverable_text``)
    without importing ``croo`` at module level. Callers construct the actual
    SDK request object from these fields at the real call site.

    Uses ``deliverable_type="text"`` with the JSON result serialized into
    ``deliverable_text``: the official croo-sdk README's only concrete
    DeliverOrderRequest example does exactly this (a JSON-shaped string
    passed as deliverable_text under DeliverableType.TEXT). SCHEMA is
    documented only as "inline schema content describing the deliverable"
    with no working example, so it is not used here to avoid guessing an
    unproven wire format.
    """

    deliverable_type: Literal["text"] = "text"
    deliverable_schema: Literal[""] = ""
    deliverable_text: str


def build_cap_delivery_mapping(
    *,
    risk_response: RiskCheckResponse,
    proof: LocalDeliveryProof,
) -> CAPDeliveryMapping:
    """Map existing Aegis risk evidence into a text-type CAP delivery payload.

    Reuses ``risk_response``/``proof`` as computed by the existing risk engine
    and proof builder; invents no transaction hash, settlement ID, escrow ID,
    or reputation score. The local proof ledger remains the authoritative
    Aegis evidence source — this only republishes it into the CAP shape.
    """
    payload = {
        "decision": risk_response.decision.value,
        "risk_score": risk_response.risk_score,
        "confidence": risk_response.confidence.value,
        "safe_to_execute": risk_response.safe_to_execute,
        "suggested_action": risk_response.suggested_action,
        "proof_id": proof.proof_id,
        "risk_factors": [
            factor.model_dump(mode="json") for factor in risk_response.risk_factors
        ],
        "reasons": risk_response.reasons,
        "market_regime": risk_response.market_regime,
        "request_hash": proof.request_hash,
        "response_hash": proof.response_hash,
        "result_hash": proof.result_hash,
        "policy_version": proof.policy_version,
        "created_at": proof.created_at.isoformat(),
    }
    deliverable_text = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return CAPDeliveryMapping(deliverable_text=deliverable_text)
