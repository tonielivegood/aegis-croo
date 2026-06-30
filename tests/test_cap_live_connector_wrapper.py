import ast
from decimal import Decimal
from pathlib import Path

import pytest

from src.aegis_croo.cap.config import ControlledProviderRuntimeConfig
from src.aegis_croo.cap.controlled_provider_runtime import (
    ControlledProviderRuntime,
)
from src.aegis_croo.cap.live_connector_wrapper import (
    LiveConnectorWrapper,
    LiveConnectorWrapperRequest,
)
from src.aegis_croo.cap.pilot_readiness import (
    PilotGateSnapshot,
    PilotReadinessRequest,
    PilotRunLockRegistry,
    SanitizedDashboardStatus,
)


class FakeProviderStream:
    def __init__(
        self,
        *,
        registration_error: Exception | None = None,
        close_error: Exception | None = None,
    ) -> None:
        self.handler = None
        self.registration_calls = 0
        self.close_calls = 0
        self.registration_error = registration_error
        self.close_error = close_error
        self.reconnecting = False

    def on_any(self, handler) -> None:
        self.registration_calls += 1
        if self.registration_error is not None:
            raise self.registration_error
        self.handler = handler

    async def close(self) -> None:
        self.close_calls += 1
        if self.close_error is not None:
            raise self.close_error

    def err(self):
        return None


class FakeConnector:
    def __init__(
        self,
        stream: FakeProviderStream | None = None,
        *,
        open_error: Exception | None = None,
        connect_error: Exception | None = None,
    ) -> None:
        self.stream = stream or FakeProviderStream()
        self.open_calls = 0
        self.connect_calls = 0
        self.open_error = open_error
        self.connect_error = connect_error

    async def open_stream(self) -> FakeProviderStream:
        self.open_calls += 1
        if self.open_error is not None:
            raise self.open_error
        return self.stream

    async def connect(self, _stream: FakeProviderStream) -> None:
        self.connect_calls += 1
        if self.connect_error is not None:
            raise self.connect_error


def runtime_config(**overrides) -> ControlledProviderRuntimeConfig:
    values = {
        "runtime_enabled": True,
        "accept_enabled": False,
        "reject_enabled": False,
        "paid_order_handling_enabled": False,
        "deliver_enabled": False,
        "timeout_seconds": 0.01,
        "close_timeout_seconds": 0.05,
        "max_events": 1,
    }
    values.update(overrides)
    return ControlledProviderRuntimeConfig(**values)


def ready_dashboard(**overrides) -> SanitizedDashboardStatus:
    values = {
        "profile_complete": True,
        "service_identity_verified": True,
        "service_price_usdc": Decimal("0.12"),
        "require_fund_transfer": False,
        "requirements_schema_verified": True,
        "deliverable_schema_verified": True,
        "no_pending_negotiations_or_orders": True,
    }
    values.update(overrides)
    return SanitizedDashboardStatus(**values)


def ready_option_b_gates(**overrides) -> PilotGateSnapshot:
    values = {
        "cap_mode": "real",
        "cap_pilot_enabled": True,
        "real_provider_enabled": True,
        "controlled_runtime_enabled": True,
        "observe_only_enabled": False,
        "requester_enabled": True,
        "negotiate_enabled": True,
        "pay_enabled": False,
        "accept_enabled": False,
        "reject_enabled": False,
        "paid_order_handling_enabled": False,
        "deliver_enabled": False,
        "no_retry": True,
        "runtime_timeout_seconds": 5.0,
        "close_timeout_seconds": 1.0,
        "max_events": 1,
    }
    values.update(overrides)
    return PilotGateSnapshot(**values)


def readiness_request(
    *,
    option: str = "option_b",
    dashboard: SanitizedDashboardStatus | None = None,
    gates: PilotGateSnapshot | None = None,
    **overrides,
) -> PilotReadinessRequest:
    values = {
        "option": option,
        "git_status_clean": True,
        "dashboard": dashboard or ready_dashboard(),
        "gates": gates or ready_option_b_gates(),
        "run_id": "pilot-2026-06-30-option-b1-001",
        "approval_granted": True,
        "approval_token_present": True,
    }
    values.update(overrides)
    return PilotReadinessRequest(**values)


def wrapper(connector: FakeConnector) -> LiveConnectorWrapper:
    return LiveConnectorWrapper(
        connector=connector,
        runtime=ControlledProviderRuntime(config=runtime_config()),
    )


@pytest.mark.anyio
async def test_default_state_never_connects() -> None:
    connector = FakeConnector()

    result = await wrapper(connector).run(LiveConnectorWrapperRequest())

    assert result.status == "no_go"
    assert result.connector_started is False
    assert result.close_attempted is False
    assert result.closed is False
    assert result.real_cap_ready is False
    assert result.live_execution_authorized is False
    assert connector.open_calls == 0
    assert connector.connect_calls == 0


@pytest.mark.anyio
async def test_missing_cap_pilot_enabled_prevents_connector_start() -> None:
    connector = FakeConnector()
    request = LiveConnectorWrapperRequest(
        readiness=readiness_request(
            gates=ready_option_b_gates(cap_pilot_enabled=False)
        ),
        connector_start_authorized=True,
    )

    result = await wrapper(connector).run(
        request,
        run_registry=PilotRunLockRegistry(),
    )

    assert result.status == "no_go"
    assert "master_pilot_gate_disabled" in result.reason_codes
    assert connector.open_calls == 0
    assert connector.connect_calls == 0


@pytest.mark.anyio
async def test_missing_requester_kill_switch_prevents_connector_start() -> None:
    connector = FakeConnector()
    request = LiveConnectorWrapperRequest(
        readiness=readiness_request(
            gates=ready_option_b_gates(requester_enabled=False)
        ),
        connector_start_authorized=True,
    )

    result = await wrapper(connector).run(
        request,
        run_registry=PilotRunLockRegistry(),
    )

    assert result.status == "no_go"
    assert "requester_gate_disabled" in result.reason_codes
    assert connector.open_calls == 0


@pytest.mark.anyio
async def test_missing_run_registry_prevents_connector_start() -> None:
    connector = FakeConnector()
    request = LiveConnectorWrapperRequest(
        readiness=readiness_request(),
        connector_start_authorized=True,
    )

    result = await wrapper(connector).run(request)

    assert result.status == "no_go"
    assert "run_registry_unavailable" in result.reason_codes
    assert connector.open_calls == 0


@pytest.mark.anyio
async def test_missing_dashboard_facts_prevent_connector_start() -> None:
    connector = FakeConnector()
    request = LiveConnectorWrapperRequest(
        readiness=readiness_request(dashboard=SanitizedDashboardStatus()),
        connector_start_authorized=True,
    )

    result = await wrapper(connector).run(
        request,
        run_registry=PilotRunLockRegistry(),
    )

    assert result.status == "no_go"
    assert "dashboard_check_failed" in result.reason_codes
    assert connector.open_calls == 0


@pytest.mark.anyio
async def test_option_b_approval_ready_does_not_start_without_manual_invocation() -> None:
    connector = FakeConnector()
    request = LiveConnectorWrapperRequest(readiness=readiness_request())

    result = await wrapper(connector).run(
        request,
        run_registry=PilotRunLockRegistry(),
    )

    assert result.status == "approval_ready_not_started"
    assert result.approval_ready is True
    assert result.connector_started is False
    assert result.live_execution_authorized is False
    assert connector.open_calls == 0


@pytest.mark.anyio
async def test_connector_close_is_attempted_once_on_registration_failure() -> None:
    stream = FakeProviderStream(
        registration_error=RuntimeError(
            "registration failed sdk_key=croo_sk_registration-secret"
        )
    )
    connector = FakeConnector(stream=stream)
    request = LiveConnectorWrapperRequest(
        readiness=readiness_request(),
        connector_start_authorized=True,
    )

    result = await wrapper(connector).run(
        request,
        run_registry=PilotRunLockRegistry(),
    )

    assert result.status == "runtime_error"
    assert result.connector_started is True
    assert result.close_attempted is True
    assert result.closed is True
    assert stream.registration_calls == 1
    assert stream.close_calls == 1
    assert connector.open_calls == 1
    assert connector.connect_calls == 0
    assert result.error is not None
    assert "croo_sk_" not in result.error
    assert "registration-secret" not in result.error


@pytest.mark.anyio
async def test_sanitized_evidence_returned_for_connector_setup_failure() -> None:
    connector = FakeConnector(
        open_error=RuntimeError(
            "open failed wss://croo.invalid/ws?key=croo_sk_open-secret"
        )
    )
    request = LiveConnectorWrapperRequest(
        readiness=readiness_request(),
        connector_start_authorized=True,
    )

    result = await wrapper(connector).run(
        request,
        run_registry=PilotRunLockRegistry(),
    )

    assert result.status == "setup_failed"
    assert result.connector_started is False
    assert result.close_attempted is False
    assert result.error is not None
    assert "wss://" not in result.error
    assert "croo_sk_" not in result.error
    assert "open-secret" not in result.error


@pytest.mark.anyio
async def test_option_c_remains_separate_approval_required_and_never_starts() -> None:
    option_c_gates = ready_option_b_gates(
        pay_enabled=True,
        accept_enabled=True,
        paid_order_handling_enabled=True,
        deliver_enabled=True,
        max_events=3,
    )
    connector = FakeConnector()
    request = LiveConnectorWrapperRequest(
        readiness=readiness_request(
            option="option_c",
            gates=option_c_gates,
            run_id="pilot-2026-06-30-option-c-b1-001",
        ),
        connector_start_authorized=True,
    )

    result = await wrapper(connector).run(
        request,
        run_registry=PilotRunLockRegistry(),
    )

    assert result.status == "separate_approval_required"
    assert result.approval_ready is False
    assert result.real_cap_ready is False
    assert connector.open_calls == 0


def test_live_connector_wrapper_has_no_sdk_network_or_mutating_calls() -> None:
    module_path = Path("src/aegis_croo/cap/live_connector_wrapper.py")
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    forbidden_imports = {
        "croo",
        "websocket",
        "websockets",
        "requests",
        "httpx",
        "aiohttp",
        "subprocess",
    }
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
        "connect_websocket",
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

    assert forbidden_imports.isdisjoint(imported_roots)
    assert forbidden_calls.isdisjoint(called_names)
