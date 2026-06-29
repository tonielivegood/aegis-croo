import os
from dataclasses import dataclass
from typing import Literal


CAPMode = Literal["mock", "real"]
CAP_MODE: CAPMode = "mock"
CAP_REAL_PROVIDER_ENABLED = False
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
