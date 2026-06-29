from copy import deepcopy
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from apps.api.main import app
from src.aegis_croo.oracle.risk_oracle import assess_risk
from src.aegis_croo.orders.ledger import InMemoryOrderLedger
from src.aegis_croo.orders.models import CAP_DISCLAIMER, LocalOrderRequest, OrderLifecycleStatus
from src.aegis_croo.orders.proof import build_delivery_proof, canonical_hash


client = TestClient(app)

ORDER_PAYLOAD = {
    "requester_agent_id": "mock-requester-agent",
    "provider_agent_id": "aegis-risk-oracle",
    "service_id": "aegis-risk-check-schema-v1",
    "service_name": "Aegis Risk Check",
    "sla_minutes": 5,
    "price_usdc": 0.25,
    "requirements_type": "schema",
    "deliverable_type": "schema",
    "request": {
        "token": "BNB",
        "chain": "bsc",
        "intended_action": "buy",
        "size_usd": 100,
        "market_signal": {
            "price_change_24h": -8,
            "volume_change_24h": -10,
            "liquidity_usd": 50_000,
            "volatility_24h": 9,
        },
    },
}

ORDER_RESPONSE_FIELDS = {
    "order_id", "requester_agent_id", "provider_agent_id", "service_id",
    "service_name", "status", "lifecycle", "price_usdc", "sla_minutes",
    "requirements_type", "deliverable_type", "decision", "risk_score",
    "confidence", "safe_to_execute", "risk_factors", "reasons",
    "suggested_action", "proof_id", "proof", "created_at", "completed_at",
    "cap_mode", "cap_disclaimer",
}
PROOF_FIELDS = {
    "proof_id", "order_id", "request_hash", "response_hash", "result_hash",
    "policy_version", "deliverable_type", "created_at",
}


def test_canonical_hash_is_deterministic_for_equivalent_json() -> None:
    first = {"service": "Aegis", "nested": {"b": 2, "a": 1}}
    second = {"nested": {"a": 1, "b": 2}, "service": "Aegis"}
    assert canonical_hash(first) == canonical_hash(second)
    assert len(canonical_hash(first)) == 64


def test_order_models_define_the_local_cap_contract() -> None:
    request = LocalOrderRequest.model_validate(ORDER_PAYLOAD)
    assert request.price_usdc == 0.25
    assert request.sla_minutes == 5
    assert request.requirements_type == "schema"
    assert request.deliverable_type == "schema"
    assert CAP_DISCLAIMER == (
        "Local mock ledger only. No real CAP payment, escrow, on-chain "
        "delivery, or settlement."
    )
    assert [status.value for status in OrderLifecycleStatus] == [
        "NEGOTIATED_MOCK", "LOCKED_MOCK", "DELIVERED", "CLEARED_MOCK",
    ]


def test_delivery_proof_hashes_request_response_and_result_payloads() -> None:
    request = LocalOrderRequest.model_validate(ORDER_PAYLOAD)
    risk_response = assess_risk(request.request)
    created_at = datetime(2026, 6, 29, 12, 0, tzinfo=UTC)
    proof = build_delivery_proof(
        proof_id="proof_test", order_id="order_test",
        request_payload=request.model_dump(mode="json"),
        risk_response=risk_response, created_at=created_at,
    )
    repeated = build_delivery_proof(
        proof_id="proof_other", order_id="order_other",
        request_payload=request.model_dump(mode="json"),
        risk_response=risk_response,
        created_at=datetime(2026, 6, 30, 12, 0, tzinfo=UTC),
    )
    assert set(proof.model_dump(mode="json")) == PROOF_FIELDS
    assert proof.deliverable_type == "schema"
    assert all(len(value) == 64 for value in (
        proof.request_hash, proof.response_hash, proof.result_hash
    ))
    assert proof.request_hash == repeated.request_hash
    assert proof.response_hash == repeated.response_hash
    assert proof.result_hash == repeated.result_hash


def test_ledger_creates_and_stores_a_cleared_mock_order_and_proof() -> None:
    ledger = InMemoryOrderLedger()
    order = ledger.create_order(LocalOrderRequest.model_validate(ORDER_PAYLOAD))
    proof = ledger.get_proof(order.proof_id)
    assert order.order_id.startswith("order_")
    assert order.proof_id.startswith("proof_")
    assert order.status is OrderLifecycleStatus.CLEARED_MOCK
    assert order.lifecycle == list(OrderLifecycleStatus)
    assert order.decision.value == "BLOCK"
    assert order.cap_mode == "local_mock"
    assert order.cap_disclaimer == CAP_DISCLAIMER
    assert order.created_at.tzinfo is not None
    assert order.completed_at >= order.created_at
    assert ledger.get_order(order.order_id) == order
    assert proof is not None
    assert order.proof == proof
    assert proof.order_id == order.order_id
    assert ledger.get_order("order_missing") is None
    assert ledger.get_proof("proof_missing") is None


def test_ledger_hashes_are_stable_for_equivalent_orders() -> None:
    ledger = InMemoryOrderLedger()
    first = ledger.create_order(LocalOrderRequest.model_validate(ORDER_PAYLOAD))
    second = ledger.create_order(LocalOrderRequest.model_validate(deepcopy(ORDER_PAYLOAD)))
    assert first.order_id != second.order_id
    assert first.proof_id != second.proof_id
    assert first.proof.request_hash == second.proof.request_hash
    assert first.proof.response_hash == second.proof.response_hash
    assert first.proof.result_hash == second.proof.result_hash


def post_order(payload: dict) -> dict:
    response = client.post("/orders", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == ORDER_RESPONSE_FIELDS
    assert set(body["proof"]) == PROOF_FIELDS
    return body


def test_post_order_creates_and_get_routes_return_stored_records() -> None:
    body = post_order(ORDER_PAYLOAD)
    assert body["status"] == "CLEARED_MOCK"
    assert body["lifecycle"] == [
        "NEGOTIATED_MOCK", "LOCKED_MOCK", "DELIVERED", "CLEARED_MOCK",
    ]
    assert body["decision"] == "BLOCK"
    assert body["cap_mode"] == "local_mock"
    assert body["cap_disclaimer"] == CAP_DISCLAIMER
    assert all(len(body["proof"][field]) == 64 for field in (
        "request_hash", "response_hash", "result_hash"
    ))

    order_response = client.get(f"/orders/{body['order_id']}")
    proof_response = client.get(f"/proof/{body['proof_id']}")
    assert order_response.status_code == 200
    assert order_response.json() == body
    assert proof_response.status_code == 200
    assert proof_response.json() == body["proof"]


def test_safe_small_buy_order_returns_execute() -> None:
    payload = deepcopy(ORDER_PAYLOAD)
    payload["request"]["market_signal"] = {
        "price_change_24h": 1,
        "volume_change_24h": 8,
        "liquidity_usd": 500_000,
        "volatility_24h": 2,
    }
    body = post_order(payload)
    assert body["decision"] == "EXECUTE"
    assert body["risk_score"] < 35
    assert body["safe_to_execute"] is True


def test_unknown_order_and_proof_return_404() -> None:
    assert client.get("/orders/order_missing").status_code == 404
    assert client.get("/proof/proof_missing").status_code == 404


def test_order_response_has_no_forbidden_capabilities() -> None:
    body = post_order(ORDER_PAYLOAD)
    forbidden = {
        "execution", "wallet", "private_key", "signing", "swap",
        "transaction", "broadcast",
    }
    assert forbidden.isdisjoint(body.keys())
    assert forbidden.isdisjoint(body["proof"].keys())
