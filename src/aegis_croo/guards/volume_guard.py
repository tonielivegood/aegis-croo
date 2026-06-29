from src.aegis_croo.guards.base import BaseGuard
from src.aegis_croo.schemas.risk import RiskCheckRequest, RiskFactor, RiskSeverity


class VolumeGuard(BaseGuard):
    def evaluate(self, request: RiskCheckRequest) -> RiskFactor | None:
        if request.intended_action.casefold() != "buy" or request.market_signal is None:
            return None
        change = request.market_signal.volume_change_24h
        if change is None:
            return None
        if change < 0:
            return RiskFactor(
                name="negative_volume_confirmation",
                severity=RiskSeverity.MEDIUM,
                score_impact=35,
                evidence=f"Buy signal has negative 24h volume change of {change:.1f}%.",
            )
        if change < 5:
            return RiskFactor(
                name="weak_volume_confirmation",
                severity=RiskSeverity.LOW,
                score_impact=15,
                evidence=f"Buy signal has weak 24h volume confirmation of {change:.1f}%.",
            )
        return None
