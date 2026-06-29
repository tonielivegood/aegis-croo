import hashlib
import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from src.aegis_croo.orders.models import LocalDeliveryProof
from src.aegis_croo.schemas.risk import RiskCheckResponse


def _json_value(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    return value


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        _json_value(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_delivery_proof(
    *,
    proof_id: str,
    order_id: str,
    request_payload: dict[str, Any],
    risk_response: RiskCheckResponse,
    created_at: datetime,
) -> LocalDeliveryProof:
    response_payload = risk_response.model_dump(mode="json")
    result_payload = {
        "deliverable_type": "schema",
        "deliverable": response_payload,
    }
    return LocalDeliveryProof(
        proof_id=proof_id,
        order_id=order_id,
        request_hash=canonical_hash(request_payload),
        response_hash=canonical_hash(response_payload),
        result_hash=canonical_hash(result_payload),
        policy_version=risk_response.proof.policy_version,
        deliverable_type="schema",
        created_at=created_at,
    )
