from src.aegis_croo.guards.base import BaseGuard
from src.aegis_croo.schemas.risk import RiskCheckRequest, RiskFactor, RiskSeverity


class LiquidityGuard(BaseGuard):
    def evaluate(self, request: RiskCheckRequest) -> RiskFactor | None:
        liquidity = request.market_signal.liquidity_usd if request.market_signal else None
        if liquidity is None:
            return RiskFactor(
                name="missing_liquidity",
                severity=RiskSeverity.MEDIUM,
                score_impact=35,
                evidence="Liquidity data is missing from the market signal.",
            )
        ratio = float("inf") if liquidity == 0 and request.size_usd > 0 else (
            request.size_usd / liquidity if liquidity else 0.0
        )
        if ratio > 0.05:
            return RiskFactor(
                name="liquidity_impact",
                severity=RiskSeverity.HIGH,
                score_impact=70,
                evidence=f"Order-to-liquidity ratio is {ratio:.3f}, above 0.05.",
            )
        if ratio > 0.01:
            return RiskFactor(
                name="liquidity_impact",
                severity=RiskSeverity.MEDIUM,
                score_impact=35,
                evidence=f"Order-to-liquidity ratio is {ratio:.3f}, above 0.01.",
            )
        return None
