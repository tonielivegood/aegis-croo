import ast
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.aegis_croo.cap.gated_real_sdk_adapter import (
    GatedRealCROOSDKAdapter,
    RealCROOSDKCredentials,
    RealSDKAdapterBlocked,
    RealSDKGateSnapshot,
)
from src.aegis_croo.cap.option_b_pilot_runner import (
    OptionBNegotiationPilotRequest,
)
from src.aegis_croo.cap.pilot_readiness import (
    PilotGateSnapshot,
    PilotReadinessRequest,
    SanitizedDashboardStatus,
)
from src.aegis_croo.cap.quarantined_sdk_connector import (
    QuarantinedConnectorRequest,
    QuarantinedSDKNegotiationConnector,
)


class FakeRunRegistry:
    def contains(self, _run_id: str) -> bool:
        return False


class RecordingImporter:
    def __init__(self, module=None, error: Exception | None = None) -> None:
        self.module = module
        self.error = error
        self.calls = []

    def __call__(self, name: str):
        self.calls.append(name)
        if self.error is not None:
            raise self.error
        return self.module


class RecordingCredentialsProvider:
    def __init__(
        self,
        credentials: RealCROOSDKCredentials | None = None,
        error: Exception | None = None,
    ) -> None:
        self.credentials = credentials or fake_credentials()
        self.error = error
        self.calls = 0

    def __call__(self) -> RealCROOSDKCredentials:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.credentials


class FakeSDKEvent:
    def __init__(self, *, event_type: str, raw=None, **attributes) -> None:
        self.type = event_type
        self.raw = dict(raw or {})
        for name, value in attributes.items():
            setattr(self, name, value)


class FakeSDKEventStream:
    def __init__(
        self,
        *,
        event: FakeSDKEvent | None = None,
        registration_error: Exception | None = None,
        close_error: Exception | None = None,
        stream_error: Exception | None = None,
    ) -> None:
        self.event = event
        self.registration_error = registration_error
        self.close_error = close_error
        self.stream_error = stream_error
        self.registration_calls = 0
        self.close_calls = 0

    def on_any(self, handler) -> None:
        self.registration_calls += 1
        if self.registration_error is not None:
            raise self.registration_error
        if self.event is not None:
            handler(self.event)

    async def close(self) -> None:
        self.close_calls += 1
        if self.close_error is not None:
            raise self.close_error

    def err(self):
        return self.stream_error


class FakeSDKState:
    def __init__(
        self,
        *,
        stream: FakeSDKEventStream | None = None,
        client_error: Exception | None = None,
        connect_error: Exception | None = None,
    ) -> None:
        self.stream = stream or FakeSDKEventStream()
        self.client_error = client_error
        self.connect_error = connect_error
        self.config_calls = []
        self.client_calls = []
        self.connect_calls = 0
        self.client_close_calls = 0


def fake_sdk_module(state: FakeSDKState):
    class Config:
        def __init__(self, *, base_url: str, ws_url: str) -> None:
            state.config_calls.append((base_url, ws_url))
            self.base_url = base_url
            self.ws_url = ws_url

    class AgentClient:
        def __init__(self, config, sdk_key: str) -> None:
            state.client_calls.append((config, sdk_key))
            if state.client_error is not None:
                raise state.client_error

        async def connect_websocket(self):
            state.connect_calls += 1
            if state.connect_error is not None:
                raise state.connect_error
            return state.stream

        async def close(self) -> None:
            state.client_close_calls += 1

    return SimpleNamespace(Config=Config, AgentClient=AgentClient)


def fake_credentials(**overrides) -> RealCROOSDKCredentials:
    values = {
        "api_url": "https://api.example.test",
        "ws_url": "wss://ws.example.test/events",
        "sdk_key": "croo_sk_fake-only",
        "service_id": "service-fake-only",
        "provider_agent_id": "provider-fake-only",
    }
    values.update(overrides)
    return RealCROOSDKCredentials(**values)


def ready_adapter_gates(**overrides) -> RealSDKGateSnapshot:
    values = {
        "cap_mode": "real",
        "cap_pilot_enabled": True,
        "connector_start_authorized": True,
        "sdk_load_authorized": True,
        "option_b_negotiation_pilot_authorized": True,
        "require_fund_transfer": False,
        "accept_enabled": False,
        "reject_enabled": False,
        "pay_enabled": False,
        "deliver_enabled": False,
        "upload_enabled": False,
        "settle_enabled": False,
        "clear_enabled": False,
    }
    values.update(overrides)
    return RealSDKGateSnapshot(**values)


def ready_dashboard() -> SanitizedDashboardStatus:
    return SanitizedDashboardStatus(
        profile_complete=True,
        service_identity_verified=True,
        service_price_usdc=Decimal("0.12"),
        require_fund_transfer=False,
        requirements_schema_verified=True,
        deliverable_schema_verified=True,
        no_pending_negotiations_or_orders=True,
    )


def ready_pilot_request() -> OptionBNegotiationPilotRequest:
    return OptionBNegotiationPilotRequest(
        readiness=PilotReadinessRequest(
            option="option_b",
            git_status_clean=True,
            dashboard=ready_dashboard(),
            gates=PilotGateSnapshot(
                cap_mode="real",
                cap_pilot_enabled=True,
                real_provider_enabled=True,
                controlled_runtime_enabled=True,
                observe_only_enabled=False,
                requester_enabled=True,
                negotiate_enabled=True,
                pay_enabled=False,
                accept_enabled=False,
                reject_enabled=False,
                paid_order_handling_enabled=False,
                deliver_enabled=False,
                no_retry=True,
                runtime_timeout_seconds=0.05,
                close_timeout_seconds=0.05,
                max_events=1,
            ),
            run_id="pilot-2026-06-30-option-b2c-001",
            approval_granted=True,
            approval_token_present=True,
        ),
        connector_start_authorized=True,
        requester_kill_switch_enabled=True,
    )


def boundary_request() -> QuarantinedConnectorRequest:
    return QuarantinedConnectorRequest(
        pilot=ready_pilot_request(),
        sdk_load_authorized=True,
    )


def negotiation_event(**raw_overrides) -> FakeSDKEvent:
    raw = {
        "type": "order_negotiation_created",
        "service_id": "wrong-service",
        "service_name": "Untrusted",
        "requirements_type": "schema",
        "requirements": {},
    }
    raw.update(raw_overrides)
    return FakeSDKEvent(
        event_type="order_negotiation_created",
        raw=raw,
        negotiation_id="raw-negotiation-id",
    )


def build_adapter(
    *,
    gates: RealSDKGateSnapshot | None = None,
    state: FakeSDKState | None = None,
    importer_error: Exception | None = None,
    credentials: RealCROOSDKCredentials | None = None,
):
    state = state or FakeSDKState()
    importer = RecordingImporter(
        fake_sdk_module(state),
        error=importer_error,
    )
    credentials_provider = RecordingCredentialsProvider(credentials)
    adapter = GatedRealCROOSDKAdapter(
        gates=gates or ready_adapter_gates(),
        credentials_provider=credentials_provider,
        importer=importer,
    )
    return adapter, importer, credentials_provider, state


def test_module_import_and_adapter_construction_do_not_import_sdk() -> None:
    adapter, importer, credentials_provider, state = build_adapter()

    assert adapter is not None
    assert importer.calls == []
    assert credentials_provider.calls == 0
    assert state.client_calls == []
    assert state.connect_calls == 0


def test_safe_defaults_block_sdk_loading() -> None:
    importer = RecordingImporter(SimpleNamespace())
    credentials_provider = RecordingCredentialsProvider()
    adapter = GatedRealCROOSDKAdapter(
        gates=RealSDKGateSnapshot(),
        credentials_provider=credentials_provider,
        importer=importer,
    )

    with pytest.raises(RealSDKAdapterBlocked) as exc_info:
        adapter.load_client()

    assert "real_mode_required" in exc_info.value.reason_codes
    assert importer.calls == []
    assert credentials_provider.calls == 0


@pytest.mark.parametrize(
    ("gate_override", "reason"),
    [
        ({"cap_mode": "mock"}, "real_mode_required"),
        ({"cap_pilot_enabled": False}, "master_pilot_gate_disabled"),
        ({"connector_start_authorized": False}, "connector_start_not_authorized"),
        ({"sdk_load_authorized": False}, "sdk_load_not_authorized"),
        (
            {"option_b_negotiation_pilot_authorized": False},
            "option_b_pilot_not_authorized",
        ),
        ({"require_fund_transfer": True}, "fund_transfer_enabled"),
        ({"accept_enabled": True}, "mutation_gate_enabled"),
        ({"reject_enabled": True}, "mutation_gate_enabled"),
        ({"pay_enabled": True}, "mutation_gate_enabled"),
        ({"deliver_enabled": True}, "mutation_gate_enabled"),
        ({"upload_enabled": True}, "mutation_gate_enabled"),
        ({"settle_enabled": True}, "mutation_gate_enabled"),
        ({"clear_enabled": True}, "mutation_gate_enabled"),
    ],
)
def test_missing_or_unsafe_gate_blocks_before_import(gate_override, reason) -> None:
    adapter, importer, credentials_provider, _ = build_adapter(
        gates=ready_adapter_gates(**gate_override)
    )

    with pytest.raises(RealSDKAdapterBlocked) as exc_info:
        adapter.load_client()

    assert reason in exc_info.value.reason_codes
    assert importer.calls == []
    assert credentials_provider.calls == 0


def test_all_gates_allow_lazy_fake_sdk_client_construction_only() -> None:
    adapter, importer, credentials_provider, state = build_adapter()

    client = adapter.load_client()

    assert importer.calls == ["croo"]
    assert credentials_provider.calls == 1
    assert len(state.config_calls) == 1
    assert len(state.client_calls) == 1
    assert state.connect_calls == 0
    assert client is not None


def test_returned_client_exposes_no_lifecycle_mutation_methods() -> None:
    client = build_adapter()[0].load_client()
    forbidden = {
        "negotiate_order",
        "accept_negotiation",
        "accept_negotiation_with_fund_address",
        "reject_negotiation",
        "pay_order",
        "deliver_order",
        "reject_order",
        "upload_file",
        "get_download_url",
        "settle_order",
        "clear_order",
    }

    assert all(not hasattr(client, name) for name in forbidden)


@pytest.mark.anyio
async def test_negotiation_event_routes_through_quarantine_to_option_b() -> None:
    state = FakeSDKState(stream=FakeSDKEventStream(event=negotiation_event()))
    adapter, _, _, state = build_adapter(state=state)

    result = await QuarantinedSDKNegotiationConnector(
        sdk_loader=adapter.load_client
    ).run(boundary_request(), run_registry=FakeRunRegistry())

    assert result.status == "manual_review"
    assert result.runner_result is not None
    assert result.runner_result.status == "manual_review_simulated"
    assert result.live_execution_authorized is False
    assert result.mutating_methods_called is False
    assert result.real_cap_ready is False
    assert state.connect_calls == 1
    assert state.stream.registration_calls == 1
    assert state.stream.close_calls == 1
    assert state.client_close_calls == 1


@pytest.mark.anyio
@pytest.mark.parametrize(
    "event_type",
    [
        "order_paid",
        "paid_order",
        "order_delivered",
        "order_settled",
        "unknown_event",
        "",
        None,
    ],
)
async def test_non_negotiation_sdk_events_fail_closed(event_type) -> None:
    event = FakeSDKEvent(event_type=event_type, raw={"type": event_type})
    state = FakeSDKState(stream=FakeSDKEventStream(event=event))
    adapter, _, _, _ = build_adapter(state=state)

    result = await QuarantinedSDKNegotiationConnector(
        sdk_loader=adapter.load_client
    ).run(boundary_request(), run_registry=FakeRunRegistry())

    assert result.status == "no_go"
    assert result.reason_codes == ["unsupported_event_type"]
    assert result.runner_result is None
    assert result.mutating_methods_called is False


@pytest.mark.anyio
async def test_sdk_import_failure_returns_fixed_sanitized_evidence() -> None:
    adapter, _, _, _ = build_adapter(
        importer_error=RuntimeError(
            "wss://user:secret@example/ws?key=croo_sk_import-secret"
        )
    )

    result = await QuarantinedSDKNegotiationConnector(
        sdk_loader=adapter.load_client
    ).run(boundary_request(), run_registry=FakeRunRegistry())

    assert result.status == "setup_failed"
    assert result.error == "sdk_import_failed"
    assert "croo_sk_import-secret" not in result.model_dump_json()
    assert "wss://" not in result.model_dump_json()


@pytest.mark.anyio
async def test_client_construction_failure_returns_fixed_sanitized_evidence() -> None:
    state = FakeSDKState(
        client_error=RuntimeError(
            "service-secret provider-secret X-SDK-Key: croo_sk_client-secret"
        )
    )
    adapter, _, _, _ = build_adapter(state=state)

    result = await QuarantinedSDKNegotiationConnector(
        sdk_loader=adapter.load_client
    ).run(boundary_request(), run_registry=FakeRunRegistry())

    assert result.status == "setup_failed"
    assert result.error == "sdk_client_init_failed"
    evidence = result.model_dump_json()
    assert "service-secret" not in evidence
    assert "provider-secret" not in evidence
    assert "croo_sk_client-secret" not in evidence


@pytest.mark.anyio
async def test_sdk_registration_failure_closes_once_with_sanitized_evidence() -> None:
    stream = FakeSDKEventStream(
        registration_error=RuntimeError(
            "Authorization: raw-header croo_sk_registration-secret"
        )
    )
    state = FakeSDKState(stream=stream)
    adapter, _, _, _ = build_adapter(state=state)

    result = await QuarantinedSDKNegotiationConnector(
        sdk_loader=adapter.load_client
    ).run(boundary_request(), run_registry=FakeRunRegistry())

    assert result.status == "stream_error"
    assert result.error == "sdk_stream_registration_failed"
    assert result.closed is True
    assert stream.close_calls == 1
    assert state.client_close_calls == 1
    assert "croo_sk_registration-secret" not in result.model_dump_json()


@pytest.mark.anyio
async def test_all_secret_surfaces_are_absent_from_evidence() -> None:
    credentials = fake_credentials(
        api_url="https://api.example.test/service-secret",
        ws_url="wss://user:pass@example.test/ws?key=croo_sk_query-secret",
        sdk_key="croo_sk_sdk-secret",
        service_id="service-secret",
        provider_agent_id="provider-secret",
    )
    event = negotiation_event(
        negotiation_id="raw-event-id",
        callback_url="wss://event.example/ws?token=raw-query-secret",
        authorization="Bearer raw-header-secret",
        requirements={
            "token": "croo_sk_payload-secret",
            "chain": "ethereum",
            "intended_action": "evaluate",
            "size_usd": 1,
        },
    )
    state = FakeSDKState(stream=FakeSDKEventStream(event=event))
    adapter, _, _, _ = build_adapter(state=state, credentials=credentials)

    result = await QuarantinedSDKNegotiationConnector(
        sdk_loader=adapter.load_client
    ).run(boundary_request(), run_registry=FakeRunRegistry())

    evidence = result.model_dump_json()
    for secret in (
        "croo_sk_sdk-secret",
        "croo_sk_query-secret",
        "service-secret",
        "provider-secret",
        "raw-event-id",
        "raw-query-secret",
        "raw-header-secret",
        "croo_sk_payload-secret",
        "wss://",
        "X-SDK-Key",
    ):
        assert secret not in evidence


def test_adapter_has_no_module_time_sdk_import_or_mutating_calls() -> None:
    module_path = Path("src/aegis_croo/cap/gated_real_sdk_adapter.py")
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    forbidden_calls = {
        "negotiate_order",
        "accept_negotiation",
        "accept_negotiation_with_fund_address",
        "reject_negotiation",
        "pay_order",
        "deliver_order",
        "reject_order",
        "upload_file",
        "get_download_url",
        "settle_order",
        "clear_order",
    }
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    called_names = {
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Attribute, ast.Name))
    }

    assert "croo" not in imported_roots
    assert forbidden_calls.isdisjoint(called_names)


def test_application_paths_do_not_reference_real_sdk_adapter() -> None:
    module_name = "gated_real_sdk_adapter"
    references = []
    for path in Path("src/aegis_croo").rglob("*.py"):
        if path.name == "gated_real_sdk_adapter.py":
            continue
        if module_name in path.read_text(encoding="utf-8"):
            references.append(path)

    assert references == []
