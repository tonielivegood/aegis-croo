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
        "#05080f",
        "#57e6a5",
        "#ff4d5e",
        "#f2b84b",
        "#a9b8c2",
        "#1c2c42",
    ):
        assert token in stylesheet.casefold()

    assert ".decision--block" in stylesheet
    assert ".decision--wait" in stylesheet
    assert ".decision--execute" in stylesheet
    assert ".request-state--error" in stylesheet


def test_console_explains_buyer_and_a2a_workflows() -> None:
    page = unescape(client.get("/").text)

    for value in (
        "Call Aegis before your agent acts.",
        "One request. One decision. Proof your agent can inspect.",
        "Caller agent",
        "Aegis Risk Check",
        "Decision + proof",
        "Caller-controlled branch",
    ):
        assert value in page


def test_console_exposes_three_local_risk_scenario_presets() -> None:
    page = client.get("/").text
    script = client.get("/static/app.js").text

    for scenario in ("execute", "wait", "block"):
        assert f'data-scenario="{scenario}"' in page

    assert "RISK_SCENARIOS" in script
    assert 'querySelectorAll("[data-scenario]")' in script
    assert 'setAttribute("aria-pressed"' in script
    assert "Selected scenario changes the editable input only" in page


def test_demo_scenario_payloads_are_deterministic() -> None:
    base_request = {
        "token": "BNB",
        "chain": "bsc",
        "intended_action": "buy",
        "size_usd": 100,
        "market_signal": {
            "price_change_24h": 3.4,
            "volume_change_24h": 8.1,
            "liquidity_usd": 500_000,
            "slippage_bps": 40,
            "gas_level": "medium",
        },
        "portfolio_context": {
            "current_exposure_usd": 250,
            "max_position_usd": 1_000,
        },
    }

    for expected, volatility in (("EXECUTE", 2), ("WAIT", 8), ("BLOCK", 12)):
        payload = {
            **base_request,
            "market_signal": {
                **base_request["market_signal"],
                "volatility_24h": volatility,
            },
        }
        response = client.post("/risk-check", json=payload)

        assert response.status_code == 200
        assert response.json()["decision"] == expected


def test_proof_hashes_remain_exact_when_visually_shortened() -> None:
    page = client.get("/").text
    script = client.get("/static/app.js").text

    assert "Full values remain available to copy." in page
    assert "function setCopyValue" in script
    assert "source.dataset.fullValue || source.textContent" in script
    assert 'button.setAttribute("aria-label"' in script


def test_readiness_matrix_and_examples_remain_honest_and_self_contained() -> None:
    page = unescape(client.get("/").text)

    for value in (
        "Available now",
        "Gated / manual",
        "Not claimed",
        "Pilot price positioning",
        "CAP_MODE=mock",
        "real_cap_ready=false",
        "live_execution_authorized=false",
        "mutating_methods_called=false",
        "Branch on the decision",
    ):
        assert value in page

    assert "@risk-request.json" not in page
    assert "@mock-order.json" not in page

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
