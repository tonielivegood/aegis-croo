from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

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
MOCK_STATUS_DISCLAIMER = (
    "Mock CAP adapter only. No real CROO SDK payment, escrow, settlement, "
    "reputation, or on-chain delivery."
)
REAL_PENDING_DISCLAIMER = (
    "Real CAP mode requested, but credentials or service configuration are "
    "missing. No real CAP action was performed."
)
STEP_6B_MINIMAL_REASON = (
    "Dashboard service may be configured and SDK runtime initialization is "
    "verified. Local provider guard and adapter skeletons exist but are disabled "
    "and disconnected; Agent online WebSocket heartbeat and real CAP "
    "payment/escrow/delivery/settlement are not verified."
)
CAP_ENV_KEYS = [
    "CAP_MODE", "CROO_API_URL", "CROO_WS_URL", "CROO_SDK_KEY",
    "CROO_SERVICE_ID", "CROO_PROVIDER_AGENT_ID", "CAP_REAL_PROVIDER_ENABLED",
]
UNSAFE_SDK_METHODS = [
    "negotiate_order",
    "accept_negotiation",
    "accept_negotiation_with_fund_address",
    "reject_negotiation",
    "pay_order",
    "deliver_order",
    "reject_order",
    "upload_file",
    "get_download_url",
]
UNVERIFIED_REAL_STATUS_FIELDS = {
    "agent_online_status": "not_verified",
    "websocket_heartbeat_status": "not_verified",
    "controlled_provider_status": "local_guard_and_adapter_skeleton_disabled",
    "real_order_lifecycle_status": "not_verified",
}


def clear_cap_env(monkeypatch) -> None:
    for key in CAP_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)



def set_real_cap_env(monkeypatch, sdk_key: str = "do-not-return-this-test-value") -> None:
    monkeypatch.setenv("CAP_MODE", "real")
    monkeypatch.setenv("CROO_API_URL", "https://cap.example.test")
    monkeypatch.setenv("CROO_WS_URL", "wss://cap.example.test/ws")
    monkeypatch.setenv("CROO_SDK_KEY", sdk_key)
    monkeypatch.setenv("CROO_SERVICE_ID", "svc_test")
    monkeypatch.setenv("CROO_PROVIDER_AGENT_ID", "aegis-risk-oracle")


def install_fake_croo_sdk(monkeypatch, calls: list) -> None:
    class FakeConfig:
        def __init__(self, base_url: str, ws_url: str = "", rpc_url: str = "") -> None:
            calls.append(("Config", base_url, ws_url, rpc_url))
            self.base_url = base_url
            self.ws_url = ws_url
            self.rpc_url = rpc_url

    class FakeAgentClient:
        def __init__(self, config: FakeConfig, sdk_key: str) -> None:
            calls.append(("AgentClient", config.base_url, config.ws_url, sdk_key))

        def __getattr__(self, name: str):
            if name in UNSAFE_SDK_METHODS:
                def unsafe_method(*args, **kwargs):
                    calls.append((name, args, kwargs))
                    raise AssertionError(f"unsafe SDK method called: {name}")

                return unsafe_method
            raise AttributeError(name)

    fake_module = SimpleNamespace(AgentClient=FakeAgentClient, Config=FakeConfig)

    def fake_import_module(name: str):
        if name == "croo":
            calls.append(("import_module", name))
            return fake_module
        raise ModuleNotFoundError(name)

    monkeypatch.setattr("src.aegis_croo.cap.adapter.import_module", fake_import_module)


def post_cap_order(payload: dict) -> dict:
    response = client.post("/cap/order", json=payload)
    assert response.status_code == 200
    return response.json()


def test_cap_status_default_mock_mode(monkeypatch) -> None:
    clear_cap_env(monkeypatch)

    response = client.get("/cap/status")

    assert response.status_code == 200
    assert response.json() == {
        "cap_mode": "mock",
        "real_cap_ready": False,
        "adapter_status": "MOCK_ONLY",
        "sdk_import_status": "not_required_in_mock_mode",
        "service_id_status": "missing_or_not_required",
        "credential_status": "missing_or_not_required",
        "provider_agent_id": "aegis-risk-oracle",
        "disclaimer": MOCK_STATUS_DISCLAIMER,
    }


def test_cap_status_real_mode_with_missing_credentials(monkeypatch) -> None:
    clear_cap_env(monkeypatch)
    monkeypatch.setenv("CAP_MODE", "real")

    response = client.get("/cap/status")
    body = response.json()

    assert response.status_code == 200
    assert body["cap_mode"] == "real"
    assert body["real_cap_ready"] is False
    assert body["adapter_status"] == "REAL_CAP_PENDING_CREDENTIALS"
    assert body["missing"] == [
        "CROO_API_URL", "CROO_WS_URL", "CROO_SDK_KEY", "CROO_SERVICE_ID",
    ]
    assert body["credential_status"] == "missing"
    assert body["service_id_status"] == "missing"
    assert body["provider_agent_id"] == "aegis-risk-oracle"
    assert body["disclaimer"] == REAL_PENDING_DISCLAIMER



def test_cap_status_real_mode_missing_sdk_returns_false(monkeypatch) -> None:
    clear_cap_env(monkeypatch)
    set_real_cap_env(monkeypatch)

    def fake_import_module(name: str):
        if name == "croo":
            raise ModuleNotFoundError(name)
        raise AssertionError(f"unexpected import: {name}")

    monkeypatch.setattr("src.aegis_croo.cap.adapter.import_module", fake_import_module)

    response = client.get("/cap/status")
    body = response.json()

    assert response.status_code == 200
    assert body["cap_mode"] == "real"
    assert body["real_cap_ready"] is False
    assert body["sdk_import_status"] == "missing_package"
    assert body["client_init_status"] == "not_attempted"
    assert body["adapter_status"] == "REAL_CAP_SDK_MISSING"
    assert "do-not-return-this-test-value" not in response.text


def test_cap_status_fake_sdk_init_success_is_not_real_ready(monkeypatch) -> None:
    clear_cap_env(monkeypatch)
    set_real_cap_env(monkeypatch)
    calls = []
    install_fake_croo_sdk(monkeypatch, calls)

    response = client.get("/cap/status")
    body = response.json()

    assert response.status_code == 200
    assert body["cap_mode"] == "real"
    assert body["real_cap_ready"] is False
    assert body["sdk_import_status"] == "ok"
    assert body["client_init_status"] == "ok"
    assert body["adapter_status"] == "REAL_CAP_CLIENT_INITIALIZED_READINESS_UNVERIFIED"
    assert body["readiness_reason"] == STEP_6B_MINIMAL_REASON
    for field, value in UNVERIFIED_REAL_STATUS_FIELDS.items():
        assert body[field] == value
    assert body["service_id_status"] == "present_unverified"
    assert body["credential_status"] == "present"
    assert "do-not-return-this-test-value" not in response.text
    assert ("import_module", "croo") in calls
    assert any(call[0] == "AgentClient" for call in calls)
    assert all(call[0] not in UNSAFE_SDK_METHODS for call in calls)


def test_cap_status_fake_sdk_init_success_does_not_fake_cap_success(monkeypatch) -> None:
    clear_cap_env(monkeypatch)
    set_real_cap_env(monkeypatch)
    calls = []
    install_fake_croo_sdk(monkeypatch, calls)

    response = client.get("/cap/status")
    serialized = response.text.lower()

    assert response.status_code == 200
    assert response.json()["real_cap_ready"] is False
    assert "agent online websocket heartbeat" in serialized
    assert "controlled provider behavior" in serialized
    assert "real cap payment/escrow/delivery/settlement" in serialized
    assert "payment verified" not in serialized
    assert "escrow verified" not in serialized
    assert "settlement verified" not in serialized
    assert all(call[0] not in UNSAFE_SDK_METHODS for call in calls)


def test_cap_status_does_not_expose_secret_values(monkeypatch) -> None:
    clear_cap_env(monkeypatch)
    set_real_cap_env(monkeypatch)

    response = client.get("/cap/status")
    serialized = response.text

    assert response.status_code == 200
    assert "do-not-return-this-test-value" not in serialized
    assert response.json()["credential_status"] == "present"


def test_cap_status_does_not_require_croo_sdk_in_local_tests(monkeypatch) -> None:
    clear_cap_env(monkeypatch)

    response = client.get("/cap/status")

    assert response.status_code == 200
    assert response.json()["sdk_import_status"] == "not_required_in_mock_mode"


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
        if path.name != "provider_guard.py"
    ).lower()

    forbidden_terms = {
        "import croo", "from croo", "private_key",
        "sign_transaction", "send_raw_transaction", "broadcast_transaction",
        "swap(", "wallet =", "live_trading", "execute_trade", "place_order",
        "send_transaction",
    }
    assert all(term not in scanned_text for term in forbidden_terms)
