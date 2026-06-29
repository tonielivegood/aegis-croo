import hashlib
import json
from typing import Any

from src.aegis_croo.config import POLICY_VERSION
from src.aegis_croo.guards import DEFAULT_GUARDS
from src.aegis_croo.schemas.common import Confidence, Decision
from src.aegis_croo.schemas.risk import (
    Proof,
    RiskCheckRequest,
    RiskCheckResponse,
    RiskFactor,
)


IMPORTANT_SIGNAL_FIELDS = (
    "price_change_24h",
    "volume_change_24h",
    "liquidity_usd",
    "volatility_24h",
)


def _canonical_hash(value: dict[str, Any]) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _decision_for_score(risk_score: int) -> Decision:
    if risk_score >= 70:
        return Decision.BLOCK
    if risk_score >= 35:
        return Decision.WAIT
    return Decision.EXECUTE


def _missing_signal_fields(request: RiskCheckRequest) -> list[str]:
    signal = request.market_signal
    if signal is None:
        return list(IMPORTANT_SIGNAL_FIELDS)
    return [
        field for field in IMPORTANT_SIGNAL_FIELDS if getattr(signal, field) is None
    ]


def _evaluate_guards(request: RiskCheckRequest) -> list[RiskFactor]:
    factors: list[RiskFactor] = []
    for guard in DEFAULT_GUARDS:
        factor = guard.evaluate(request)
        if factor is not None:
            factors.append(factor)
    return factors


def _confidence_for(
    missing_fields: list[str], factors: list[RiskFactor]
) -> Confidence:
    if missing_fields:
        return Confidence.LOW
    if any(factor.name == "unknown_token_or_market" for factor in factors):
        return Confidence.MEDIUM
    return Confidence.HIGH


def _market_regime(
    request: RiskCheckRequest,
    decision: Decision,
    factors: list[RiskFactor],
    missing_fields: list[str],
) -> str:
    names = {factor.name for factor in factors}
    if "suspicious_pump" in names:
        return "suspicious_pump"
    if "unknown_token_or_market" in names:
        return "unknown_market"
    if "high_slippage" in names:
        return "high_slippage"
    if "portfolio_overexposure" in names:
        return "overexposed_portfolio"
    if missing_fields:
        return "missing_data"
    if (
        request.intended_action.casefold() == "buy"
        and "high_volatility" in names
    ):
        return "volatile_buy"
    if (
        decision is Decision.EXECUTE
        and request.intended_action.casefold() == "buy"
        and request.size_usd <= 100
        and not factors
    ):
        return "safe_small_buy"
    if decision is Decision.BLOCK:
        return "elevated_risk"
    if decision is Decision.WAIT:
        return "uncertain_market"
    return "stable_market"


def _reasons_for(
    factors: list[RiskFactor], missing_fields: list[str]
) -> list[str]:
    reasons = [factor.evidence for factor in factors]
    if missing_fields:
        reasons.append(
            "Important market data is missing: " + ", ".join(missing_fields) + "."
        )
    if not reasons:
        reasons.append("No guard identified elevated risk in the supplied evidence.")
    return reasons


def _suggested_action(decision: Decision) -> str:
    if decision is Decision.BLOCK:
        return "BLOCK this proposed action and reassess the flagged risk evidence."
    if decision is Decision.WAIT:
        return "WAIT for stronger or more complete evidence before proceeding."
    return (
        "EXECUTE means the risk decision is acceptable; Aegis performs no "
        "transaction or execution."
    )


def assess_risk(request: RiskCheckRequest) -> RiskCheckResponse:
    request_payload = request.model_dump(mode="json")
    request_hash = _canonical_hash(request_payload)
    factors = _evaluate_guards(request)
    missing_fields = _missing_signal_fields(request)
    risk_score = min(100, sum(factor.score_impact for factor in factors))
    if missing_fields:
        risk_score = max(35, risk_score)
    decision = _decision_for_score(risk_score)
    confidence = _confidence_for(missing_fields, factors)

    response_payload = {
        "decision": decision.value,
        "risk_score": risk_score,
        "confidence": confidence.value,
        "market_regime": _market_regime(
            request, decision, factors, missing_fields
        ),
        "safe_to_execute": decision is Decision.EXECUTE,
        "risk_factors": [factor.model_dump(mode="json") for factor in factors],
        "reasons": _reasons_for(factors, missing_fields),
        "suggested_action": _suggested_action(decision),
    }
    response_hash = _canonical_hash(
        {
            **response_payload,
            "proof": {
                "request_hash": request_hash,
                "policy_version": POLICY_VERSION,
            },
        }
    )

    return RiskCheckResponse(
        **response_payload,
        proof=Proof(
            request_hash=request_hash,
            response_hash=response_hash,
            policy_version=POLICY_VERSION,
        ),
    )
