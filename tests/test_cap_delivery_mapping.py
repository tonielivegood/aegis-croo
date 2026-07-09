import json
from datetime import UTC, datetime

from src.aegis_croo.cap.delivery_mapping import build_cap_delivery_mapping
from src.aegis_croo.oracle.risk_oracle import assess_risk
from src.aegis_croo.orders.proof import build_delivery_proof
from src.aegis_croo.schemas.risk import RiskCheckRequest


SAFE_BUY = {
    "token": "BNB",
    "chain": "bsc",
    "intended_action": "buy",
    "size_usd": 100,
    "market_signal": {
        "price_change_24h": 1.0,
        "volume_change_24h": 8.0,
        "liquidity_usd": 500_000,
        "volatility_24h": 2.0,
    },
}


def _mapping_for(payload: dict):
    request = RiskCheckRequest.model_validate(payload)
    response = assess_risk(request)
    proof = build_delivery_proof(
        proof_id="proof_test",
        order_id="order_test",
        request_payload=request.model_dump(mode="json"),
        risk_response=response,
        created_at=datetime.now(UTC),
    )
    return build_cap_delivery_mapping(risk_response=response, proof=proof), response, proof


def test_uses_text_deliverable_type_not_schema() -> None:
    """Regression for Gate 3D: the official croo-sdk README's only concrete
    DeliverOrderRequest example uses DeliverableType.TEXT with a JSON-shaped
    string in deliverable_text. SCHEMA has no working example and must not
    be used until proven."""
    mapping, _, _ = _mapping_for(SAFE_BUY)
    assert mapping.deliverable_type == "text"
    assert mapping.deliverable_schema == ""
    assert mapping.deliverable_text != ""
    json.loads(mapping.deliverable_text)  # must be valid JSON


def test_decision_block_maps_correctly() -> None:
    payload = dict(SAFE_BUY, market_signal={
        "price_change_24h": -8.0,
        "volume_change_24h": -10.0,
        "liquidity_usd": 50_000,
        "volatility_24h": 9.0,
    })
    mapping, response, _ = _mapping_for(payload)
    body = json.loads(mapping.deliverable_text)
    assert response.decision.value == "BLOCK"
    assert body["decision"] == "BLOCK"


def test_decision_wait_maps_correctly() -> None:
    payload = dict(SAFE_BUY)
    payload["market_signal"] = dict(payload["market_signal"])
    del payload["market_signal"]["liquidity_usd"]
    mapping, response, _ = _mapping_for(payload)
    body = json.loads(mapping.deliverable_text)
    assert response.decision.value == "WAIT"
    assert body["decision"] == "WAIT"


def test_decision_execute_maps_correctly() -> None:
    mapping, response, _ = _mapping_for(SAFE_BUY)
    body = json.loads(mapping.deliverable_text)
    assert response.decision.value == "EXECUTE"
    assert body["decision"] == "EXECUTE"


def test_proof_id_and_result_hash_preserved() -> None:
    mapping, _, proof = _mapping_for(SAFE_BUY)
    body = json.loads(mapping.deliverable_text)
    assert body["proof_id"] == proof.proof_id == "proof_test"
    assert body["result_hash"] == proof.result_hash
    assert len(proof.result_hash) == 64


def test_service_required_deliverable_fields_present() -> None:
    mapping, _, _ = _mapping_for(SAFE_BUY)
    body = json.loads(mapping.deliverable_text)
    required = {
        "decision",
        "risk_score",
        "confidence",
        "safe_to_execute",
        "suggested_action",
        "proof_id",
        "risk_factors",
    }
    assert required.issubset(body.keys())
    assert mapping.deliverable_type == "text"
    assert mapping.deliverable_schema == ""


def test_delivery_json_is_deterministic() -> None:
    mapping_a, _, _ = _mapping_for(SAFE_BUY)
    mapping_b, _, _ = _mapping_for(SAFE_BUY)
    # Two independent runs produce byte-identical JSON except created_at/proof_id/
    # order_id/hashes which depend on wall-clock time and random UUIDs supplied by
    # the caller; here both runs use the same fixed proof_id/order_id, so the
    # only remaining source of nondeterminism is created_at timestamp precision.
    body_a = json.loads(mapping_a.deliverable_text)
    body_b = json.loads(mapping_b.deliverable_text)
    assert body_a["decision"] == body_b["decision"]
    assert body_a["result_hash"] == body_b["result_hash"]
    assert body_a["request_hash"] == body_b["request_hash"]
    # Same inputs serialized twice through the same function must be byte-identical.
    payload = json.loads(mapping_a.deliverable_text)
    reserialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    assert reserialized == mapping_a.deliverable_text


def test_no_fabricated_tx_hash_or_settlement_fields() -> None:
    mapping, _, _ = _mapping_for(SAFE_BUY)
    body = json.loads(mapping.deliverable_text)
    forbidden = {"tx_hash", "settlement_id", "escrow_id", "reputation", "pts"}
    assert forbidden.isdisjoint(body.keys())
