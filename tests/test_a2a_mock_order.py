from collections.abc import Callable
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from src.aegis_croo.agents.mock_execution_agent import (
    MockExecutionAgent,
    MockExecutionStatus,
)
from src.aegis_croo.schemas.common import Confidence, Decision
from src.aegis_croo.schemas.risk import Proof, RiskCheckRequest, RiskCheckResponse


client = TestClient(app)

SAFE_REQUEST = RiskCheckRequest.model_validate(
    {
        "token": "BNB",
        "chain": "bsc",
        "intended_action": "buy",
        "size_usd": 100,
        "market_signal": {
            "price_change_24h": 1,
            "volume_change_24h": 8,
            "liquidity_usd": 500_000,
            "volatility_24h": 2,
        },
    }
)

SAFE_ORDER = {
    "buyer_agent_id": "mock-execution-agent",
    "requested_action": SAFE_REQUEST.model_dump(mode="json"),
}


def oracle_response(decision: Decision) -> RiskCheckResponse:
    score = {Decision.BLOCK: 70, Decision.WAIT: 35, Decision.EXECUTE: 0}[decision]
    return RiskCheckResponse(
        decision=decision,
        risk_score=score,
        confidence=Confidence.HIGH,
        market_regime="test_fixture",
        safe_to_execute=decision is Decision.EXECUTE,
        risk_factors=[],
        reasons=["Deterministic test oracle response."],
        suggested_action="Test only.",
        proof=Proof(
            request_hash="a" * 64,
            response_hash="b" * 64,
            policy_version="test-policy",
        ),
    )


@pytest.mark.parametrize(
    ("decision", "expected_status"),
    [
        (Decision.BLOCK, MockExecutionStatus.REFUSED),
        (Decision.WAIT, MockExecutionStatus.DELAYED),
        (Decision.EXECUTE, MockExecutionStatus.SIMULATED_EXECUTION_ONLY),
    ],
)
def test_agent_calls_oracle_before_mapping_mock_status(
    decision: Decision,
    expected_status: MockExecutionStatus,
) -> None:
    received_requests: list[RiskCheckRequest] = []

    def assessor(request: RiskCheckRequest) -> RiskCheckResponse:
        received_requests.append(request)
        return oracle_response(decision)

    result = MockExecutionAgent(risk_assessor=assessor).process_order(
        "mock-execution-agent", SAFE_REQUEST
    )

    assert received_requests == [SAFE_REQUEST]
    assert result.aegis_decision is decision
    assert result.mock_execution_status is expected_status
    assert result.safe_to_execute is (decision is Decision.EXECUTE)


def test_agent_uses_a_risk_assessor_callable() -> None:
    assessor: Callable[[RiskCheckRequest], RiskCheckResponse] = lambda request: (
        oracle_response(Decision.WAIT)
    )
    result = MockExecutionAgent(assessor).process_order(
        "mock-execution-agent", SAFE_REQUEST
    )
    assert result.mock_execution_status is MockExecutionStatus.DELAYED
    assert "delayed" in result.reason.lower()


def post_mock_order(payload: dict) -> dict:
    response = client.post("/a2a/mock-order", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "buyer_agent_id",
        "aegis_decision",
        "risk_score",
        "safe_to_execute",
        "mock_execution_status",
        "reason",
        "risk_factors",
        "proof",
    }
    assert set(body["proof"]) == {
        "request_hash",
        "response_hash",
        "policy_version",
    }
    for factor in body["risk_factors"]:
        assert set(factor) == {"name", "severity", "score_impact", "evidence"}
    return body


def test_volatile_buy_is_refused() -> None:
    payload = deepcopy(SAFE_ORDER)
    payload["requested_action"]["market_signal"] = {
        "price_change_24h": -8,
        "volume_change_24h": -10,
        "liquidity_usd": 50_000,
        "volatility_24h": 9,
    }
    body = post_mock_order(payload)
    assert body["buyer_agent_id"] == "mock-execution-agent"
    assert body["aegis_decision"] == "BLOCK"
    assert body["risk_score"] >= 70
    assert body["safe_to_execute"] is False
    assert body["mock_execution_status"] == "REFUSED"
    assert body["risk_factors"]


def test_missing_data_is_delayed() -> None:
    payload = deepcopy(SAFE_ORDER)
    del payload["requested_action"]["market_signal"]["liquidity_usd"]
    body = post_mock_order(payload)
    assert body["aegis_decision"] == "WAIT"
    assert 35 <= body["risk_score"] < 70
    assert body["safe_to_execute"] is False
    assert body["mock_execution_status"] == "DELAYED"


def test_safe_small_buy_is_simulated_only() -> None:
    body = post_mock_order(SAFE_ORDER)
    assert body["aegis_decision"] == "EXECUTE"
    assert body["risk_score"] < 35
    assert body["safe_to_execute"] is True
    assert body["mock_execution_status"] == "SIMULATED_EXECUTION_ONLY"
    assert "submits nothing" in body["reason"]


def test_unknown_token_is_refused() -> None:
    payload = deepcopy(SAFE_ORDER)
    payload["requested_action"]["token"] = "UNKNOWN"
    body = post_mock_order(payload)
    assert body["aegis_decision"] == "BLOCK"
    assert body["safe_to_execute"] is False
    assert body["mock_execution_status"] == "REFUSED"
    assert any(
        factor["name"] == "unknown_token_or_market"
        for factor in body["risk_factors"]
    )
