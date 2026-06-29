from src.aegis_croo.guards.base import BaseGuard
from src.aegis_croo.schemas.risk import RiskCheckRequest, RiskFactor, RiskSeverity


class SuspiciousPumpGuard(BaseGuard):
    def evaluate(self, request: RiskCheckRequest) -> RiskFactor | None:
        signal = request.market_signal
        if (
            signal is None
            or signal.price_change_24h is None
            or signal.liquidity_usd is None
            or signal.price_change_24h <= 40
            or signal.liquidity_usd >= 50_000
        ):
            return None
        return RiskFactor(
            name="suspicious_pump",
            severity=RiskSeverity.CRITICAL,
            score_impact=100,
            evidence=(
                f"24h price change is {signal.price_change_24h:.1f}% while liquidity "
                f"is only ${signal.liquidity_usd:.2f}."
            ),
        )
