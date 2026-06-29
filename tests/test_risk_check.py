from copy import deepcopy

from fastapi.testclient import TestClient

from apps.api.main import app


client = TestClient(app)

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


def post_risk_check(payload: dict) -> dict:
    response = client.post("/risk-check", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "decision",
        "risk_score",
        "confidence",
        "market_regime",
        "safe_to_execute",
        "risk_factors",
        "reasons",
        "suggested_action",
        "proof",
    }
    assert set(body["proof"]) == {
        "request_hash",
        "response_hash",
        "policy_version",
    }
    assert len(body["proof"]["request_hash"]) == 64
    assert len(body["proof"]["response_hash"]) == 64
    assert body["proof"]["policy_version"] == "aegis-risk-oracle-v0.1"
    for factor in body["risk_factors"]:
        assert set(factor) == {"name", "severity", "score_impact", "evidence"}
    return body


def test_volatile_buy_returns_block() -> None:
    payload = deepcopy(SAFE_BUY)
    payload["market_signal"] = {
        "price_change_24h": -8.0,
        "volume_change_24h": -10.0,
        "liquidity_usd": 50_000,
        "volatility_24h": 9.0,
    }
    body = post_risk_check(payload)
    assert body["decision"] == "BLOCK"
    assert body["risk_score"] >= 70
    assert body["safe_to_execute"] is False
    assert body["market_regime"] == "volatile_buy"
    assert {factor["name"] for factor in body["risk_factors"]} >= {
        "high_volatility",
        "negative_volume_confirmation",
    }


def test_safe_small_buy_returns_execute() -> None:
    body = post_risk_check(SAFE_BUY)
    assert body["decision"] == "EXECUTE"
    assert body["risk_score"] < 35
    assert body["safe_to_execute"] is True
    assert body["market_regime"] == "safe_small_buy"
    assert body["risk_factors"] == []
    assert "risk decision" in body["suggested_action"].lower()
    assert "executor" not in body["suggested_action"].lower()


def test_missing_important_market_data_returns_wait() -> None:
    payload = deepcopy(SAFE_BUY)
    del payload["market_signal"]["liquidity_usd"]
    body = post_risk_check(payload)
    assert body["decision"] == "WAIT"
    assert 35 <= body["risk_score"] < 70
    assert body["safe_to_execute"] is False
    assert body["market_regime"] == "missing_data"
    assert body["confidence"] == "low"
    assert body["risk_factors"][0]["name"] == "missing_liquidity"


def test_unknown_token_returns_block() -> None:
    payload = deepcopy(SAFE_BUY)
    payload["token"] = "UNKNOWN"
    body = post_risk_check(payload)
    assert body["decision"] == "BLOCK"
    assert body["risk_score"] >= 70
    assert body["safe_to_execute"] is False
    assert body["market_regime"] == "unknown_market"
    assert body["risk_factors"][0]["name"] == "unknown_token_or_market"


def test_high_slippage_returns_block() -> None:
    payload = deepcopy(SAFE_BUY)
    payload["market_signal"]["slippage_bps"] = 601
    body = post_risk_check(payload)
    assert body["decision"] == "BLOCK"
    assert body["risk_score"] >= 70
    assert body["market_regime"] == "high_slippage"
    assert body["risk_factors"][0]["name"] == "high_slippage"


def test_suspicious_pump_returns_block() -> None:
    payload = deepcopy(SAFE_BUY)
    payload["market_signal"]["price_change_24h"] = 41
    payload["market_signal"]["liquidity_usd"] = 49_999
    body = post_risk_check(payload)
    assert body["decision"] == "BLOCK"
    assert body["risk_score"] == 100
    assert body["market_regime"] == "suspicious_pump"
    assert any(factor["name"] == "suspicious_pump" for factor in body["risk_factors"])


def test_overexposed_portfolio_does_not_execute() -> None:
    payload = deepcopy(SAFE_BUY)
    payload["portfolio_context"] = {
        "current_exposure_usd": 950,
        "max_position_usd": 1_000,
    }
    body = post_risk_check(payload)
    assert body["decision"] != "EXECUTE"
    assert body["safe_to_execute"] is False
    assert body["market_regime"] == "overexposed_portfolio"
    assert body["risk_factors"][0]["name"] == "portfolio_overexposure"
