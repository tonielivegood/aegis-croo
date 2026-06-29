from src.aegis_croo.guards.base import BaseGuard
from src.aegis_croo.schemas.risk import RiskCheckRequest, RiskFactor, RiskSeverity


class GasGuard(BaseGuard):
    def evaluate(self, request: RiskCheckRequest) -> RiskFactor | None:
        gas_level = request.market_signal.gas_level if request.market_signal else None
        if gas_level == "critical":
            return RiskFactor(
                name="elevated_gas",
                severity=RiskSeverity.HIGH,
                score_impact=70,
                evidence="Reported gas level is critical.",
            )
        if gas_level == "high":
            return RiskFactor(
                name="elevated_gas",
                severity=RiskSeverity.MEDIUM,
                score_impact=35,
                evidence="Reported gas level is high.",
            )
        return None
