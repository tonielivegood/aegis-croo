from src.aegis_croo.guards.base import BaseGuard
from src.aegis_croo.schemas.risk import RiskCheckRequest, RiskFactor, RiskSeverity


class ExposureGuard(BaseGuard):
    def evaluate(self, request: RiskCheckRequest) -> RiskFactor | None:
        context = request.portfolio_context
        if context is None:
            return None
        projected = context.current_exposure_usd + request.size_usd
        if projected <= context.max_position_usd:
            return None
        return RiskFactor(
            name="portfolio_overexposure",
            severity=RiskSeverity.HIGH,
            score_impact=70,
            evidence=(
                f"Projected exposure ${projected:.2f} exceeds maximum "
                f"${context.max_position_usd:.2f}."
            ),
        )
