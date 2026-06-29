from copy import deepcopy

import pytest

from src.aegis_croo.guards.exposure_guard import ExposureGuard
from src.aegis_croo.guards.gas_guard import GasGuard
from src.aegis_croo.guards.liquidity_guard import LiquidityGuard
from src.aegis_croo.guards.slippage_guard import SlippageGuard
from src.aegis_croo.guards.suspicious_pump_guard import SuspiciousPumpGuard
from src.aegis_croo.guards.unknown_token_guard import UnknownTokenGuard
from src.aegis_croo.guards.volatility_guard import VolatilityGuard
from src.aegis_croo.guards.volume_guard import VolumeGuard
from src.aegis_croo.schemas.risk import RiskCheckRequest


BASE_REQUEST = {
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


def request_with(**changes: object) -> RiskCheckRequest:
    payload = deepcopy(BASE_REQUEST)
    signal_changes = changes.pop("market_signal", None)
    payload.update(changes)
    if signal_changes is not None:
        payload["market_signal"].update(signal_changes)
    return RiskCheckRequest.model_validate(payload)


@pytest.mark.parametrize(
    ("guard", "risk_request", "name", "severity", "impact", "evidence_fragment"),
    [
        (VolatilityGuard(), request_with(market_signal={"volatility_24h": 7}), "high_volatility", "medium", 35, "7.0"),
        (LiquidityGuard(), request_with(size_usd=30_000), "liquidity_impact", "high", 70, "0.060"),
        (VolumeGuard(), request_with(market_signal={"volume_change_24h": -1}), "negative_volume_confirmation", "medium", 35, "-1.0"),
        (ExposureGuard(), request_with(portfolio_context={"current_exposure_usd": 950, "max_position_usd": 1_000}), "portfolio_overexposure", "high", 70, "1050.00"),
        (SlippageGuard(), request_with(market_signal={"slippage_bps": 601}), "high_slippage", "high", 70, "601.0"),
        (GasGuard(), request_with(market_signal={"gas_level": "critical"}), "elevated_gas", "high", 70, "critical"),
        (UnknownTokenGuard(), request_with(token="UNKNOWN"), "unknown_token_or_market", "high", 70, "bsc:UNKNOWN"),
        (SuspiciousPumpGuard(), request_with(market_signal={"price_change_24h": 41, "liquidity_usd": 49_999}), "suspicious_pump", "critical", 100, "41.0"),
    ],
)
def test_each_guard_returns_an_explainable_factor(
    guard: object,
    risk_request: RiskCheckRequest,
    name: str,
    severity: str,
    impact: int,
    evidence_fragment: str,
) -> None:
    factor = guard.evaluate(risk_request)

    assert factor is not None
    assert factor.name == name
    assert factor.severity.value == severity
    assert factor.score_impact == impact
    assert evidence_fragment in factor.evidence


def test_volatility_guard_returns_critical_factor_at_twelve() -> None:
    factor = VolatilityGuard().evaluate(request_with(market_signal={"volatility_24h": 12}))
    assert factor is not None
    assert factor.severity.value == "critical"
    assert factor.score_impact == 70


def test_missing_liquidity_returns_wait_sized_factor() -> None:
    factor = LiquidityGuard().evaluate(request_with(market_signal={"liquidity_usd": None}))
    assert factor is not None
    assert factor.name == "missing_liquidity"
    assert factor.severity.value == "medium"
    assert factor.score_impact == 35
    assert "missing" in factor.evidence.lower()


def test_weak_buy_volume_returns_low_factor() -> None:
    factor = VolumeGuard().evaluate(request_with(market_signal={"volume_change_24h": 4}))
    assert factor is not None
    assert factor.severity.value == "low"
    assert factor.score_impact == 15


def test_optional_portfolio_context_does_not_block_by_itself() -> None:
    assert ExposureGuard().evaluate(request_with()) is None


@pytest.mark.parametrize(
    ("guard", "risk_request"),
    [
        (VolatilityGuard(), request_with(market_signal={"volatility_24h": 6.99})),
        (LiquidityGuard(), request_with(size_usd=5_000)),
        (VolumeGuard(), request_with(intended_action="sell", market_signal={"volume_change_24h": -10})),
        (SlippageGuard(), request_with(market_signal={"slippage_bps": 300})),
        (GasGuard(), request_with(market_signal={"gas_level": "medium"})),
        (UnknownTokenGuard(), request_with()),
        (SuspiciousPumpGuard(), request_with(market_signal={"price_change_24h": 40, "liquidity_usd": 49_999})),
    ],
)
def test_guard_returns_none_when_rule_is_not_triggered(guard: object, risk_request: RiskCheckRequest) -> None:
    assert guard.evaluate(risk_request) is None

