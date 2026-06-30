from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import ModuleType
from typing import Any, Literal, Protocol

from pydantic import BaseModel

from src.aegis_croo.cap.ws_safety import redact_sensitive_text


_SDK_MODULE_NAME = "croo"
_NEGOTIATION_CREATED = "order_negotiation_created"
_ALLOWED_EVENT_KEYS = {
    "service_id",
    "serviceId",
    "service_name",
    "serviceName",
    "requirements_type",
    "requirementsType",
    "requirements",
    "require_fund_transfer",
    "requires_fund_transfer",
    "fund_transfer_required",
    "requiresFundTransfer",
    "requireFundTransfer",
    "fundTransferRequired",
}
_SENSITIVE_KEYS = {
    "authorization",
    "proxy-authorization",
    "x-api-key",
    "x-sdk-key",
    "api_key",
    "sdk_key",
    "provider_key",
    "callback_url",
    "websocket_url",
    "negotiation_id",
    "order_id",
}


class ModuleImporter(Protocol):
    def __call__(self, name: str) -> ModuleType | Any: ...


class SDKEventStream(Protocol):
    def on_any(self, handler: Callable[[Any], None]) -> None: ...

    async def close(self) -> None: ...


class SDKAgentClient(Protocol):
    async def connect_websocket(self) -> SDKEventStream: ...

    async def close(self) -> None: ...


@dataclass(frozen=True, repr=False)
class RealCROOSDKCredentials:
    api_url: str
    ws_url: str
    sdk_key: str
    service_id: str
    provider_agent_id: str


CredentialsProvider = Callable[[], RealCROOSDKCredentials]


class RealSDKGateSnapshot(BaseModel):
    cap_mode: Literal["mock", "real"] = "mock"
    cap_pilot_enabled: bool = False
    connector_start_authorized: bool = False
    sdk_load_authorized: bool = False
    option_b_negotiation_pilot_authorized: bool = False
    require_fund_transfer: bool = False
    accept_enabled: bool = False
    reject_enabled: bool = False
    pay_enabled: bool = False
    deliver_enabled: bool = False
    upload_enabled: bool = False
    settle_enabled: bool = False
    clear_enabled: bool = False


class RealSDKAdapterError(RuntimeError):
    pass


class RealSDKAdapterBlocked(RealSDKAdapterError):
    def __init__(self, reason_codes: list[str]) -> None:
        self.reason_codes = list(dict.fromkeys(reason_codes))
        super().__init__(",".join(self.reason_codes))


class GatedRealCROOSDKAdapter:
    """Construct a narrow SDK client only after every pilot gate passes."""

    def __init__(
        self,
        *,
        gates: RealSDKGateSnapshot,
        credentials_provider: CredentialsProvider,
        importer: ModuleImporter | None = None,
    ) -> None:
        self._gates = gates
        self._credentials_provider = credentials_provider
        self._importer = importer

    def load_client(self) -> RealCROOSDKClientAdapter:
        reasons = _gate_failures(self._gates)
        if reasons:
            raise RealSDKAdapterBlocked(reasons)

        try:
            importer = self._importer or _default_importer()
            sdk_module = importer(_SDK_MODULE_NAME)
        except Exception:
            raise RealSDKAdapterError("sdk_import_failed") from None

        try:
            config_type = getattr(sdk_module, "Config")
            client_type = getattr(sdk_module, "AgentClient")
        except Exception:
            raise RealSDKAdapterError("sdk_contract_invalid") from None

        try:
            credentials = self._credentials_provider()
        except Exception:
            raise RealSDKAdapterError("sdk_credentials_unavailable") from None
        if not all(
            (
                credentials.api_url,
                credentials.ws_url,
                credentials.sdk_key,
                credentials.service_id,
                credentials.provider_agent_id,
            )
        ):
            raise RealSDKAdapterError("sdk_credentials_missing")

        try:
            config = config_type(
                base_url=credentials.api_url,
                ws_url=credentials.ws_url,
            )
            sdk_client = client_type(config, credentials.sdk_key)
        except Exception:
            raise RealSDKAdapterError("sdk_client_init_failed") from None
        return RealCROOSDKClientAdapter(sdk_client)


class RealCROOSDKClientAdapter:
    """Expose only the negotiation-stream surface required by B2-B."""

    def __init__(self, sdk_client: SDKAgentClient) -> None:
        self._sdk_client = sdk_client

    async def open_negotiation_stream(self) -> RealCROONegotiationStream:
        return RealCROONegotiationStream(self._sdk_client)


class RealCROONegotiationStream:
    """Defer the real SDK connection until B2-B calls start explicitly."""

    def __init__(self, sdk_client: SDKAgentClient) -> None:
        self._sdk_client = sdk_client
        self._handler: Callable[[Any], None] | None = None
        self._stream: SDKEventStream | None = None
        self._started = False
        self._closed = False

    def on_any(self, handler: Callable[[Any], None]) -> None:
        if self._started:
            raise RealSDKAdapterError("sdk_handler_registration_too_late")
        self._handler = handler

    async def start(self) -> None:
        if self._closed:
            raise RealSDKAdapterError("sdk_stream_closed")
        if self._started:
            raise RealSDKAdapterError("sdk_stream_already_started")
        if self._handler is None:
            raise RealSDKAdapterError("sdk_handler_missing")
        self._started = True
        try:
            self._stream = await self._sdk_client.connect_websocket()
        except Exception:
            raise RealSDKAdapterError("sdk_stream_start_failed") from None

        def dispatch(event: Any) -> None:
            handler = self._handler
            if handler is not None:
                handler(_sanitize_sdk_event(event))

        try:
            self._stream.on_any(dispatch)
        except Exception:
            raise RealSDKAdapterError(
                "sdk_stream_registration_failed"
            ) from None

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        failed = False
        try:
            if self._stream is not None:
                await self._stream.close()
        except Exception:
            failed = True
        try:
            await self._sdk_client.close()
        except Exception:
            failed = True
        if failed:
            raise RealSDKAdapterError("sdk_stream_close_failed")

    def err(self) -> str | None:
        if self._stream is None:
            return None
        error_reader = getattr(self._stream, "err", None)
        if not callable(error_reader):
            return None
        try:
            error = error_reader()
        except Exception:
            return "sdk_stream_error"
        return "sdk_stream_error" if error is not None else None


def _gate_failures(gates: RealSDKGateSnapshot) -> list[str]:
    reasons: list[str] = []
    if gates.cap_mode != "real":
        reasons.append("real_mode_required")
    if not gates.cap_pilot_enabled:
        reasons.append("master_pilot_gate_disabled")
    if not gates.connector_start_authorized:
        reasons.append("connector_start_not_authorized")
    if not gates.sdk_load_authorized:
        reasons.append("sdk_load_not_authorized")
    if not gates.option_b_negotiation_pilot_authorized:
        reasons.append("option_b_pilot_not_authorized")
    if gates.require_fund_transfer:
        reasons.append("fund_transfer_enabled")
    if any(
        (
            gates.accept_enabled,
            gates.reject_enabled,
            gates.pay_enabled,
            gates.deliver_enabled,
            gates.upload_enabled,
            gates.settle_enabled,
            gates.clear_enabled,
        )
    ):
        reasons.append("mutation_gate_enabled")
    return list(dict.fromkeys(reasons))


def _default_importer() -> ModuleImporter:
    from importlib import import_module

    return import_module


def _sanitize_sdk_event(event: Any) -> dict[str, Any]:
    raw = getattr(event, "raw", None)
    raw_mapping = raw if isinstance(raw, Mapping) else {}
    event_type = getattr(event, "type", "")
    payload: dict[str, Any] = {
        "type": event_type if isinstance(event_type, str) else ""
    }
    for key, value in raw_mapping.items():
        if key in _ALLOWED_EVENT_KEYS:
            payload[str(key)] = _sanitize_value(value)
    if "service_id" not in payload and "serviceId" not in payload:
        service_id = getattr(event, "service_id", "")
        if service_id:
            payload["service_id"] = redact_sensitive_text(str(service_id))
    return payload


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_sensitive_text(value)
    if isinstance(value, Mapping):
        return {
            str(key): _sanitize_value(item)
            for key, item in value.items()
            if str(key).casefold() not in _SENSITIVE_KEYS
        }
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, (bool, int, float)) or value is None:
        return value
    return redact_sensitive_text(str(value))
