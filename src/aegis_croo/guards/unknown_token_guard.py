from collections.abc import Iterable

from src.aegis_croo.guards.base import BaseGuard
from src.aegis_croo.schemas.risk import RiskCheckRequest, RiskFactor, RiskSeverity


DEMO_SUPPORTED_MARKETS = frozenset({("bsc", "BNB")})


class UnknownTokenGuard(BaseGuard):
    def __init__(
        self,
        supported_markets: Iterable[tuple[str, str]] = DEMO_SUPPORTED_MARKETS,
    ) -> None:
        self._supported_markets = frozenset(
            (chain.casefold(), token.upper()) for chain, token in supported_markets
        )

    def evaluate(self, request: RiskCheckRequest) -> RiskFactor | None:
        market = (request.chain.casefold(), request.token.upper())
        if market in self._supported_markets:
            return None
        return RiskFactor(
            name="unknown_token_or_market",
            severity=RiskSeverity.HIGH,
            score_impact=70,
            evidence=f"Market {market[0]}:{market[1]} is not in the trusted demo registry.",
        )
