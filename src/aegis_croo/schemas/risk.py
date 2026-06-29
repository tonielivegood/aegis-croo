from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

from src.aegis_croo.schemas.common import Confidence, Decision


class MarketSignal(BaseModel):
    price_change_24h: float | None = None
    volume_change_24h: float | None = None
    liquidity_usd: float | None = Field(default=None, ge=0)
    volatility_24h: float | None = Field(default=None, ge=0)
    slippage_bps: float | None = Field(default=None, ge=0)
    gas_level: Literal["low", "medium", "high", "critical"] | None = None


class PortfolioContext(BaseModel):
    current_exposure_usd: float = Field(ge=0)
    max_position_usd: float = Field(ge=0)


class RiskSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskFactor(BaseModel):
    name: str = Field(min_length=1)
    severity: RiskSeverity
    score_impact: int = Field(ge=0, le=100)
    evidence: str = Field(min_length=1)


class RiskCheckRequest(BaseModel):
    token: str = Field(min_length=1)
    chain: str = Field(min_length=1)
    intended_action: str = Field(min_length=1)
    size_usd: float = Field(ge=0)
    market_signal: MarketSignal | None = None
    portfolio_context: PortfolioContext | None = None


class Proof(BaseModel):
    request_hash: str
    response_hash: str
    policy_version: str


class RiskCheckResponse(BaseModel):
    decision: Decision
    risk_score: int = Field(ge=0, le=100)
    confidence: Confidence
    market_regime: str
    safe_to_execute: bool
    risk_factors: list[RiskFactor]
    reasons: list[str]
    suggested_action: str
    proof: Proof
