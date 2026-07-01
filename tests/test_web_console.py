from html import unescape

from fastapi.testclient import TestClient

from apps.api.main import app


client = TestClient(app)


def test_root_serves_aegis_web_console() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Aegis Risk Oracle" in response.text
    assert "Other agents can hire Aegis before they execute." in response.text
    assert "Aegis returns BLOCK, WAIT, or EXECUTE with proof." in response.text
    assert "form-action 'self';" in response.text
    assert '<link rel="icon" href="data:,">' in response.text


def test_console_static_assets_are_served() -> None:
    stylesheet = client.get("/static/styles.css")
    script = client.get("/static/app.js")

    assert stylesheet.status_code == 200
    assert stylesheet.headers["content-type"].startswith("text/css")
    assert script.status_code == 200
    assert "javascript" in script.headers["content-type"]


def test_console_contains_required_sections_claims_and_api_references() -> None:
    page = unescape(client.get("/").text)

    required = {
        "System posture",
        "Risk Check Console",
        "Mock A2A Order",
        "Local Order & Proof",
        "CROO Agent Store readiness",
        "Developer integration",
        "No wallet, signing, swap, transaction, or broadcast path.",
        (
            "CAP-ready gated runtime; real payment, delivery, settlement, "
            "and commercial readiness are not claimed yet."
        ),
        "0.12 USDC pilot",
        "Data & Verification Agents",
        "DeFi / On-chain Ops Agents",
        "/health",
        "/cap/status",
        "/risk-check",
        "/a2a/mock-order",
        "/orders",
        "/orders/{order_id}",
        "/proof/{proof_id}",
    }

    assert all(value in page for value in required)


def test_console_does_not_make_forbidden_product_claims() -> None:
    page = unescape(client.get("/").text).casefold()

    forbidden = {
        "connect wallet",
        "guaranteed profit",
        "guaranteed safety",
        "payment verified",
        "escrow verified",
        "settlement verified",
        "commercially ready",
        "live trading",
        "execute trade",
    }

    assert all(term not in page for term in forbidden)


def test_console_script_uses_only_safe_existing_relative_api_routes() -> None:
    script = client.get("/static/app.js").text

    for endpoint in (
        '"/health"',
        '"/cap/status"',
        '"/risk-check"',
        '"/a2a/mock-order"',
        '"/orders"',
        '`/orders/${',
        '`/proof/${',
    ):
        assert endpoint in script

    assert "innerHTML" not in script
    assert "localStorage" not in script
    assert "sessionStorage" not in script
    assert "document.cookie" not in script
    assert "/cap/order" not in script
    assert "http://" not in script
    assert "https://" not in script
    assert "dataset.decision = decision;" in script


def test_console_styles_follow_design_contract_semantic_colors() -> None:
    stylesheet = client.get("/static/styles.css").text

    for token in (
        "#070a0d",
        "#57e6a5",
        "#ff5d6c",
        "#f2b84b",
        "#a9b8c2",
        "#293a47",
    ):
        assert token in stylesheet.casefold()

    assert ".decision--block" in stylesheet
    assert ".decision--wait" in stylesheet
    assert ".decision--execute" in stylesheet
    assert ".request-state--error" in stylesheet


def test_existing_health_risk_and_cap_status_routes_remain_available(
    monkeypatch,
) -> None:
    monkeypatch.delenv("CAP_MODE", raising=False)

    health = client.get("/health")
    risk = client.post(
        "/risk-check",
        json={
            "token": "BNB",
            "chain": "bsc",
            "intended_action": "buy",
            "size_usd": 100,
            "market_signal": {
                "liquidity_usd": 500_000,
                "volatility_24h": 2,
                "slippage_bps": 40,
            },
        },
    )
    cap_status = client.get("/cap/status")

    assert health.status_code == 200
    assert risk.status_code == 200
    assert cap_status.status_code == 200
    assert cap_status.json()["cap_mode"] == "mock"
    assert cap_status.json()["real_cap_ready"] is False
