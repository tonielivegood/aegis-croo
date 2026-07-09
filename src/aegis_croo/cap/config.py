import os
from dataclasses import dataclass
from typing import Literal


CAPMode = Literal["mock", "real"]
CAP_MODE: CAPMode = "mock"
CAP_REAL_PROVIDER_ENABLED = False
CAP_WS_OBSERVE_ONLY_ENABLED = False
CAP_WS_OBSERVE_TIMEOUT_SECONDS = 5.0
CAP_WS_OBSERVE_MAX_TIMEOUT_SECONDS = 90.0
CAP_CONTROLLED_PROVIDER_RUNTIME_ENABLED = False
CAP_PROVIDER_ACCEPT_ENABLED = False
CAP_PROVIDER_REJECT_ENABLED = False
CAP_PROVIDER_PAID_ORDER_HANDLING_ENABLED = False
CAP_PROVIDER_DELIVER_ENABLED = False
CAP_PROVIDER_RUNTIME_TIMEOUT_SECONDS = 5.0
CAP_PROVIDER_RUNTIME_CLOSE_TIMEOUT_SECONDS = 1.0
CAP_PROVIDER_RUNTIME_MAX_EVENTS = 2
CAP_PROVIDER_PRESENCE_ENABLED = False
CAP_REAL_LIFECYCLE_ENABLED = False
CAP_ACCEPT_NEGOTIATION_ENABLED = False
CAP_DELIVER_ORDER_ENABLED = False
CAP_REQUESTER_CANARY_ENABLED = False
CAP_REQUESTER_PAY_ENABLED = False
LIFECYCLE_CANARY_MAX_NEGOTIATIONS = 1
LIFECYCLE_CANARY_MAX_ORDERS = 1
DEFAULT_PROVIDER_AGENT_ID = "aegis-risk-oracle"


def configured_cap_mode() -> CAPMode:
    mode = os.getenv("CAP_MODE", CAP_MODE).strip().lower()
    if mode == "real":
        return "real"
    return "mock"


def configured_real_provider_enabled() -> bool:
    value = os.getenv(
        "CAP_REAL_PROVIDER_ENABLED",
        str(CAP_REAL_PROVIDER_ENABLED),
    )
    return value.strip().lower() in {"1", "true", "yes", "on"}


def configured_ws_observe_enabled() -> bool:
    value = os.getenv(
        "CAP_WS_OBSERVE_ONLY_ENABLED",
        str(CAP_WS_OBSERVE_ONLY_ENABLED),
    )
    return value.strip().lower() in {"1", "true", "yes", "on"}


def configured_ws_observe_timeout_seconds() -> float:
    raw_value = os.getenv(
        "CAP_WS_OBSERVE_TIMEOUT_SECONDS",
        str(CAP_WS_OBSERVE_TIMEOUT_SECONDS),
    )
    try:
        value = float(raw_value)
    except ValueError:
        return CAP_WS_OBSERVE_TIMEOUT_SECONDS
    if 0 < value <= CAP_WS_OBSERVE_MAX_TIMEOUT_SECONDS:
        return value
    return CAP_WS_OBSERVE_TIMEOUT_SECONDS


class WSObserveTimeoutTooLargeError(ValueError):
    pass


def require_ws_observe_timeout_within_bounds() -> None:
    """Raise if an explicitly-set observe timeout exceeds the owner-approved ceiling.

    Non-numeric values are left to ``configured_ws_observe_timeout_seconds``'s
    existing fail-closed fallback; this only rejects an explicit, parseable,
    too-large request loudly instead of silently substituting the default.
    """
    raw_value = os.getenv("CAP_WS_OBSERVE_TIMEOUT_SECONDS")
    if raw_value is None:
        return
    try:
        value = float(raw_value)
    except ValueError:
        return
    if value > CAP_WS_OBSERVE_MAX_TIMEOUT_SECONDS:
        raise WSObserveTimeoutTooLargeError(
            "CAP_WS_OBSERVE_TIMEOUT_SECONDS must be at most "
            f"{CAP_WS_OBSERVE_MAX_TIMEOUT_SECONDS:g} seconds."
        )


def _configured_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {
        "1", "true", "yes", "on"
    }


def _configured_bounded_float(name: str, default: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if 0 < value <= 60 else default


def _configured_bounded_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if 0 < value <= 60 else default


def configured_provider_presence_enabled() -> bool:
    return _configured_bool(
        "CAP_PROVIDER_PRESENCE_ENABLED", CAP_PROVIDER_PRESENCE_ENABLED
    )


def configured_real_lifecycle_enabled() -> bool:
    return _configured_bool("CAP_REAL_LIFECYCLE_ENABLED", CAP_REAL_LIFECYCLE_ENABLED)


def configured_accept_negotiation_enabled() -> bool:
    return _configured_bool(
        "CAP_ACCEPT_NEGOTIATION_ENABLED", CAP_ACCEPT_NEGOTIATION_ENABLED
    )


def configured_deliver_order_enabled() -> bool:
    return _configured_bool("CAP_DELIVER_ORDER_ENABLED", CAP_DELIVER_ORDER_ENABLED)


def configured_requester_canary_enabled() -> bool:
    return _configured_bool(
        "CAP_REQUESTER_CANARY_ENABLED", CAP_REQUESTER_CANARY_ENABLED
    )


def configured_requester_pay_enabled() -> bool:
    return _configured_bool("CAP_REQUESTER_PAY_ENABLED", CAP_REQUESTER_PAY_ENABLED)


@dataclass(frozen=True)
class LifecycleCanaryConfig:
    """Gates and allowlist for the one-order provider lifecycle canary.

    Every mutation-capable gate defaults to False, and the allowlist values
    must be explicitly configured; nothing here enables a live connection or
    call by itself.
    """

    lifecycle_enabled: bool
    accept_enabled: bool
    deliver_enabled: bool
    expected_service_id: str | None
    expected_requester_agent_id: str | None

    @property
    def missing_allowlist(self) -> list[str]:
        missing: list[str] = []
        if not self.expected_service_id:
            missing.append("CROO_SERVICE_ID")
        if not self.expected_requester_agent_id:
            missing.append("CROO_EXPECTED_REQUESTER_AGENT_ID")
        return missing


def load_lifecycle_canary_config() -> LifecycleCanaryConfig:
    return LifecycleCanaryConfig(
        lifecycle_enabled=configured_real_lifecycle_enabled(),
        accept_enabled=configured_accept_negotiation_enabled(),
        deliver_enabled=configured_deliver_order_enabled(),
        expected_service_id=os.getenv("CROO_SERVICE_ID") or None,
        expected_requester_agent_id=os.getenv("CROO_EXPECTED_REQUESTER_AGENT_ID")
        or None,
    )


@dataclass(frozen=True)
class RequesterCanaryConfig:
    """Gates for the standalone, Aegis-Core-external requester canary script."""

    canary_enabled: bool
    pay_enabled: bool
    expected_provider_service_id: str | None

    @property
    def missing_allowlist(self) -> list[str]:
        return [] if self.expected_provider_service_id else ["CROO_SERVICE_ID"]


def load_requester_canary_config() -> RequesterCanaryConfig:
    return RequesterCanaryConfig(
        canary_enabled=configured_requester_canary_enabled(),
        pay_enabled=configured_requester_pay_enabled(),
        expected_provider_service_id=os.getenv("CROO_SERVICE_ID") or None,
    )


@dataclass(frozen=True)
class ControlledProviderRuntimeConfig:
    runtime_enabled: bool
    accept_enabled: bool
    reject_enabled: bool
    paid_order_handling_enabled: bool
    deliver_enabled: bool
    timeout_seconds: float
    close_timeout_seconds: float
    max_events: int


def load_controlled_provider_runtime_config() -> ControlledProviderRuntimeConfig:
    return ControlledProviderRuntimeConfig(
        runtime_enabled=_configured_bool(
            "CAP_CONTROLLED_PROVIDER_RUNTIME_ENABLED",
            CAP_CONTROLLED_PROVIDER_RUNTIME_ENABLED,
        ),
        accept_enabled=_configured_bool(
            "CAP_PROVIDER_ACCEPT_ENABLED", CAP_PROVIDER_ACCEPT_ENABLED
        ),
        reject_enabled=_configured_bool(
            "CAP_PROVIDER_REJECT_ENABLED", CAP_PROVIDER_REJECT_ENABLED
        ),
        paid_order_handling_enabled=_configured_bool(
            "CAP_PROVIDER_PAID_ORDER_HANDLING_ENABLED",
            CAP_PROVIDER_PAID_ORDER_HANDLING_ENABLED,
        ),
        deliver_enabled=_configured_bool(
            "CAP_PROVIDER_DELIVER_ENABLED", CAP_PROVIDER_DELIVER_ENABLED
        ),
        timeout_seconds=_configured_bounded_float(
            "CAP_PROVIDER_RUNTIME_TIMEOUT_SECONDS",
            CAP_PROVIDER_RUNTIME_TIMEOUT_SECONDS,
        ),
        close_timeout_seconds=_configured_bounded_float(
            "CAP_PROVIDER_RUNTIME_CLOSE_TIMEOUT_SECONDS",
            CAP_PROVIDER_RUNTIME_CLOSE_TIMEOUT_SECONDS,
        ),
        max_events=_configured_bounded_int(
            "CAP_PROVIDER_RUNTIME_MAX_EVENTS", CAP_PROVIDER_RUNTIME_MAX_EVENTS
        ),
    )

@dataclass(frozen=True)
class CAPProviderConfig:
    cap_mode: CAPMode
    croo_api_url: str | None
    croo_ws_url: str | None
    croo_sdk_key_present: bool
    croo_service_id: str | None
    croo_provider_agent_id: str

    @property
    def missing_real_config(self) -> list[str]:
        missing: list[str] = []
        if not self.croo_api_url:
            missing.append("CROO_API_URL")
        if not self.croo_ws_url:
            missing.append("CROO_WS_URL")
        if not self.croo_sdk_key_present:
            missing.append("CROO_SDK_KEY")
        if not self.croo_service_id:
            missing.append("CROO_SERVICE_ID")
        return missing


def load_cap_provider_config() -> CAPProviderConfig:
    return CAPProviderConfig(
        cap_mode=configured_cap_mode(),
        croo_api_url=os.getenv("CROO_API_URL") or None,
        croo_ws_url=os.getenv("CROO_WS_URL") or None,
        croo_sdk_key_present=bool(os.getenv("CROO_SDK_KEY")),
        croo_service_id=os.getenv("CROO_SERVICE_ID") or None,
        croo_provider_agent_id=os.getenv(
            "CROO_PROVIDER_AGENT_ID", DEFAULT_PROVIDER_AGENT_ID
        ),
    )
