from abc import ABC, abstractmethod

from src.aegis_croo.schemas.risk import RiskCheckRequest, RiskFactor


class BaseGuard(ABC):
    @abstractmethod
    def evaluate(self, request: RiskCheckRequest) -> RiskFactor | None:
        """Return an explainable factor when this guard is triggered."""
