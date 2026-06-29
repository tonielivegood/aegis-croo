from datetime import UTC, datetime

from src.aegis_croo.oracle.risk_oracle import assess_risk
from src.aegis_croo.orders.models import (
    CAP_DISCLAIMER,
    LocalOrderRequest,
    OrderLifecycleStatus,
)
from src.aegis_croo.orders.proof import build_delivery_proof, canonical_hash


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
        "NEGOTIATED_MOCK",
        "LOCKED_MOCK",
        "DELIVERED",
        "CLEARED_MOCK",
    ]


def test_delivery_proof_hashes_request_response_and_result_payloads() -> None:
    request = LocalOrderRequest.model_validate(ORDER_PAYLOAD)
    risk_response = assess_risk(request.request)
    created_at = datetime(2026, 6, 29, 12, 0, tzinfo=UTC)

    proof = build_delivery_proof(
        proof_id="proof_test",
        order_id="order_test",
        request_payload=request.model_dump(mode="json"),
        risk_response=risk_response,
        created_at=created_at,
    )
    repeated = build_delivery_proof(
        proof_id="proof_other",
        order_id="order_other",
        request_payload=request.model_dump(mode="json"),
        risk_response=risk_response,
        created_at=datetime(2026, 6, 30, 12, 0, tzinfo=UTC),
    )

    assert set(proof.model_dump(mode="json")) == {
        "proof_id",
        "order_id",
        "request_hash",
        "response_hash",
        "result_hash",
        "policy_version",
        "deliverable_type",
        "created_at",
    }
    assert proof.deliverable_type == "schema"
    assert len(proof.request_hash) == 64
    assert len(proof.response_hash) == 64
    assert len(proof.result_hash) == 64
    assert proof.request_hash == repeated.request_hash
    assert proof.response_hash == repeated.response_hash
    assert proof.result_hash == repeated.result_hash
