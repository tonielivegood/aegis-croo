from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from src.aegis_croo.schemas.risk import RiskCheckRequest


GuardDecision = Literal["accept_candidate", "reject", "manual_review"]

AEGIS_CAP_SERVICE_ID = "aegis-risk-check-schema-v1"
AEGIS_CAP_SERVICE_NAME = "Aegis Risk Check"
LOCAL_GUARD_DISCLAIMER = (
    "Local guard scaffold only. It does not connect WebSocket, accept orders, "
    "deliver results, settle CAP, or make Aegis online."
)

FUND_TRANSFER_KEYS = {
    "requires_fund_transfer",
    "require_fund_transfer",
    "fund_transfer_required",
    "fund_transfer",
    "needs_fund_transfer",
    "requiresFundTransfer",
    "requireFundTransfer",
    "fundTransferRequired",
    "fundTransfer",
    "needsFundTransfer",
}
TRUTHY_TEXT = {"true", "yes", "y", "1", "on", "required", "enabled"}
FALSY_TEXT = {"false", "no", "n", "0", "off", "none", "disabled", "not_required"}

FORBIDDEN_EXECUTION_PHRASES = {
    "private key",
    "private_key",
    "seed phrase",
    "seed_phrase",
    "mnemonic",
    "wallet access",
    "wallet_access",
    "connect wallet",
    "sign transaction",
    "signing request",
    "signature request",
    "transaction construction",
    "construct transaction",
    "build transaction",
    "broadcast transaction",
    "submit transaction",
    "send transaction",
    "live trading",
    "execute trade",
    "place order",
    "execute swap",
    "perform swap",
    "swap for me",
}
FORBIDDEN_EXECUTION_PATTERNS = (
    re.compile(r"\bsign(?:ing)?\s+(?:a\s+|the\s+)?transaction\b"),
    re.compile(r"\bsign(?:ing)?\b.{0,40}\b(?:order|payload|message|request)\b"),
    re.compile(r"\b(?:access|connect|use)\b.{0,40}\bwallet\b"),
    re.compile(r"\b(?:construct|build|create)\s+(?:a\s+|the\s+)?transaction\b"),
    re.compile(r"\bbroadcast\s+(?:a\s+|the\s+)?transaction\b"),
    re.compile(r"\bswap\s+[a-z0-9._-]+\s+(?:to|for)\s+[a-z0-9._-]+\b"),
    re.compile(r"\b(?:send|transfer|move|deposit)\b.{0,40}\b(?:funds?|usdc|usd|eth|btc|tokens?)\b"),
)
PROMPT_INJECTION_PHRASES = {
    "ignore previous instructions",
    "ignore all previous",
    "override aegis safety policy",
    "override safety policy",
    "bypass policy",
    "disable guard",
    "jailbreak",
    "system prompt",
    "developer message",
    "forget your instructions",
}


class CAPProviderGuardResult(BaseModel):
    decision: GuardDecision
    safe_to_accept: bool
    reason_codes: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    disclaimer: str = LOCAL_GUARD_DISCLAIMER


def evaluate_cap_provider_guard(payload: dict[str, Any]) -> CAPProviderGuardResult:
    """Evaluate a hypothetical CAP payload without touching CROO/CAP runtime APIs."""
    reject_codes: list[str] = []
    manual_codes: list[str] = []
    reasons: list[str] = []

    service_id = _first_present(payload, "service_id", "serviceId")
    service_name = _first_present(payload, "service_name", "serviceName")

    if not service_id or not service_name:
        manual_codes.append("missing_service_metadata")
        reasons.append("Service ID and name must be present before any real accept path.")
    if service_id and str(service_id).strip() != AEGIS_CAP_SERVICE_ID:
        reject_codes.append("wrong_service_id")
        reasons.append("Payload targets a service ID other than Aegis Risk Check.")
    if service_name and _normalize(service_name) != _normalize(AEGIS_CAP_SERVICE_NAME):
        reject_codes.append("wrong_service_name")
        reasons.append("Payload targets a service name other than Aegis Risk Check.")

    requirements_type = _first_present(payload, "requirements_type", "requirementsType")
    if requirements_type is None:
        manual_codes.append("missing_requirements_type")
        reasons.append("Requirements type is missing from CAP metadata.")
    elif _normalize(requirements_type) != "schema":
        reject_codes.append("invalid_requirements_schema")
        reasons.append("Aegis accepts only schema requirements for this scaffold.")

    requirements = payload.get("requirements")
    if requirements is None:
        reject_codes.append("missing_requirements_schema")
        reasons.append("Aegis requires a risk-check requirements schema.")
    elif not isinstance(requirements, dict):
        reject_codes.append("invalid_requirements_schema")
        reasons.append("Requirements must be a JSON object matching the risk-check schema.")
    else:
        try:
            RiskCheckRequest.model_validate(requirements)
        except ValidationError:
            reject_codes.append("invalid_requirements_schema")
            reasons.append("Requirements do not match the Aegis risk-check schema.")

    fund_status = _fund_transfer_status(payload)
    if fund_status == "requested":
        reject_codes.append("fund_transfer_requested")
        reasons.append("Aegis Risk Check must not require fund transfer behavior.")
    elif fund_status == "ambiguous":
        manual_codes.append("ambiguous_fund_transfer_metadata")
        reasons.append("Fund-transfer metadata is ambiguous and needs human review.")

    searchable_text = " ".join(_iter_search_text(payload)).lower()
    if _contains_forbidden_execution(searchable_text):
        reject_codes.append("forbidden_execution_request")
        reasons.append(
            "Payload requests wallet, signing, swap execution, transaction construction, "
            "broadcast, live trading, or similar execution behavior."
        )
    if _contains_any(searchable_text, PROMPT_INJECTION_PHRASES):
        reject_codes.append("prompt_injection_attempt")
        reasons.append("Payload attempts to override or bypass Aegis safety policy.")

    if reject_codes:
        return CAPProviderGuardResult(
            decision="reject",
            safe_to_accept=False,
            reason_codes=_dedupe(reject_codes + manual_codes),
            reasons=_dedupe(reasons),
        )
    if manual_codes:
        return CAPProviderGuardResult(
            decision="manual_review",
            safe_to_accept=False,
            reason_codes=_dedupe(manual_codes),
            reasons=_dedupe(reasons),
        )

    return CAPProviderGuardResult(
        decision="accept_candidate",
        safe_to_accept=True,
        reason_codes=["valid_aegis_risk_check"],
        reasons=[
            "Payload targets Aegis Risk Check, has valid schema requirements, "
            "does not request fund transfer, and contains no forbidden execution request."
        ],
    )


def _first_present(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = payload.get(key)
        if value not in (None, ""):
            return value
    return None


def _normalize(value: Any) -> str:
    return " ".join(str(value).strip().casefold().split())


def _fund_transfer_status(value: Any) -> Literal["requested", "not_requested", "ambiguous"]:
    found_ambiguous = False
    for key, item in _walk_items(value):
        if key not in FUND_TRANSFER_KEYS:
            continue
        if isinstance(item, bool):
            if item:
                return "requested"
            continue
        if item is None:
            continue
        if isinstance(item, str):
            normalized = _normalize(item).replace(" ", "_")
            if normalized in TRUTHY_TEXT:
                return "requested"
            if normalized in FALSY_TEXT:
                continue
        found_ambiguous = True
    return "ambiguous" if found_ambiguous else "not_requested"


def _walk_items(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key), item
            yield from _walk_items(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_items(item)


def _iter_search_text(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key) not in FUND_TRANSFER_KEYS:
                yield str(key).replace("_", " ")
            yield from _iter_search_text(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_search_text(item)
    elif isinstance(value, str):
        yield value


def _contains_forbidden_execution(text: str) -> bool:
    return _contains_any(text, FORBIDDEN_EXECUTION_PHRASES) or any(
        pattern.search(text) for pattern in FORBIDDEN_EXECUTION_PATTERNS
    )


def _contains_any(text: str, phrases: set[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
