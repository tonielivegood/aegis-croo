from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.main import app


client = TestClient(app)

CAP_ORDER_PAYLOAD = {
    "requester_agent_id": "mock-requester-agent",
    "provider_agent_id": "aegis-risk-oracle",
    "service_id": "aegis-risk-check-schema-v1",
    "service_name": "Aegis Risk Check",
    "sla_minutes": 5,
    "price_usdc": 0.25,
    "requirements_type": "schema",
    "deliverable_type": "schema",
    "cap_mode": "mock",
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

CAP_LIFECYCLE = [
    "NEGOTIATE_MOCK", "LOCK_MOCK", "DELIVER_LOCAL", "CLEAR_MOCK",
]
CAP_DISCLAIMER = (
    "CAP adapter mock only. No real CROO SDK payment, escrow, settlement, "
    "reputation, or on-chain delivery."
)


def post_cap_order(payload: dict) -> dict:
    response = client.post("/cap/order", json=payload)
    assert response.status_code == 200
    return response.json()


def test_cap_order_works_in_default_mock_mode() -> None:
    payload = deepcopy(CAP_ORDER_PAYLOAD)
    payload.pop("cap_mode")

    body = post_cap_order(payload)

    assert body["cap_mode"] == "mock"
    assert body["cap_adapter_status"] == "CAP_READY_LOCAL_MOCK"
    assert body["cap_lifecycle"] == CAP_LIFECYCLE
    assert body["cap_disclaimer"] == CAP_DISCLAIMER
    assert body["status"] == "CLEARED_MOCK"
    assert body["decision"] == "BLOCK"


def test_cap_order_preserves_local_order_proof_fields() -> None:
    body = post_cap_order(CAP_ORDER_PAYLOAD)

    assert body["order_id"].startswith("order_")
    assert body["proof_id"].startswith("proof_")
    assert body["proof"]["proof_id"] == body["proof_id"]
    assert body["proof"]["order_id"] == body["order_id"]
    assert all(len(body["proof"][field]) == 64 for field in (
        "request_hash", "response_hash", "result_hash",
    ))
    assert body["proof"]["policy_version"]
    assert body["proof"]["created_at"]


def test_cap_safe_small_order_returns_execute() -> None:
    payload = deepcopy(CAP_ORDER_PAYLOAD)
    payload["request"]["market_signal"] = {
        "price_change_24h": 1,
        "volume_change_24h": 8,
        "liquidity_usd": 500_000,
        "volatility_24h": 2,
    }

    body = post_cap_order(payload)

    assert body["decision"] == "EXECUTE"
    assert body["safe_to_execute"] is True
    assert body["risk_score"] < 35


def test_cap_real_mode_does_not_fake_success() -> None:
    payload = deepcopy(CAP_ORDER_PAYLOAD)
    payload["cap_mode"] = "real"

    response = client.post("/cap/order", json=payload)

    assert response.status_code == 501
    assert response.json()["detail"] == (
        "Real CROO/CAP integration is pending SDK credentials and Step 6 "
        "verification. This endpoint does not fake payment, escrow, "
        "settlement, reputation, or on-chain delivery."
    )


def test_cap_mode_environment_real_does_not_fake_success(monkeypatch) -> None:
    monkeypatch.setenv("CAP_MODE", "real")
    payload = deepcopy(CAP_ORDER_PAYLOAD)
    payload.pop("cap_mode")

    response = client.post("/cap/order", json=payload)

    assert response.status_code == 501
    assert "Real CROO/CAP integration is pending" in response.json()["detail"]


def test_cap_response_has_no_forbidden_execution_capabilities() -> None:
    body = post_cap_order(CAP_ORDER_PAYLOAD)
    forbidden = {
        "execution", "wallet", "private_key", "signing", "swap",
        "transaction", "broadcast",
    }

    assert forbidden.isdisjoint(body.keys())
    assert forbidden.isdisjoint(body["proof"].keys())


def test_cap_adapter_has_no_real_sdk_or_live_execution_path() -> None:
    scanned_roots = [Path("src"), Path("apps"), Path("examples")]
    scanned_text = "\n".join(
        path.read_text(encoding="utf-8")
        for root in scanned_roots
        for path in root.rglob("*.py")
    ).lower()

    forbidden_terms = {
        "croo-sdk", "import croo", "from croo", "private_key",
        "sign_transaction", "send_raw_transaction", "broadcast_transaction",
        "swap(", "wallet =", "live_trading", "execute_trade", "place_order",
        "send_transaction",
    }
    assert all(term not in scanned_text for term in forbidden_terms)