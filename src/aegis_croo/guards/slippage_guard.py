from src.aegis_croo.guards.base import BaseGuard
from src.aegis_croo.schemas.risk import RiskCheckRequest, RiskFactor, RiskSeverity


class SlippageGuard(BaseGuard):
    def evaluate(self, request: RiskCheckRequest) -> RiskFactor | None:
        slippage = request.market_signal.slippage_bps if request.market_signal else None
        if slippage is None or slippage <= 300:
            return None
        if slippage > 600:
            return RiskFactor(
                name="high_slippage",
                severity=RiskSeverity.HIGH,
                score_impact=70,
                evidence=f"Expected slippage is {slippage:.1f} bps, above 600 bps.",
            )
        return RiskFactor(
            name="high_slippage",
            severity=RiskSeverity.MEDIUM,
            score_impact=35,
            evidence=f"Expected slippage is {slippage:.1f} bps, above 300 bps.",
        )
