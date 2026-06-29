from src.aegis_croo.guards.base import BaseGuard
from src.aegis_croo.schemas.risk import RiskCheckRequest, RiskFactor, RiskSeverity


class VolatilityGuard(BaseGuard):
    def evaluate(self, request: RiskCheckRequest) -> RiskFactor | None:
        volatility = (
            request.market_signal.volatility_24h if request.market_signal else None
        )
        if volatility is None or volatility < 7:
            return None
        if volatility >= 12:
            return RiskFactor(
                name="high_volatility",
                severity=RiskSeverity.CRITICAL,
                score_impact=70,
                evidence=f"24h volatility is {volatility:.1f}, at or above 12.0.",
            )
        return RiskFactor(
            name="high_volatility",
            severity=RiskSeverity.MEDIUM,
            score_impact=35,
            evidence=f"24h volatility is {volatility:.1f}, at or above 7.0.",
        )
