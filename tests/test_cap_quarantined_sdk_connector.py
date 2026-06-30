import ast
from decimal import Decimal
from pathlib import Path

import pytest

from src.aegis_croo.cap.option_b_pilot_runner import (
    OptionBNegotiationPilotRequest,
    OptionBNegotiationPilotRunner,
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


class FakeStream:
    def __init__(
        self,
        *,
        event=None,
        registration_error: Exception | None = None,
        start_error: Exception | None = None,
        close_error: Exception | None = None,
        stream_error: Exception | None = None,
        block: bool = False,
    ) -> None:
        self.event = event
        self.registration_error = registration_error
        self.start_error = start_error
        self.close_error = close_error
        self.stream_error = stream_error
        self.block = block
        self.handler = None
        self.registration_calls = 0
        self.start_calls = 0
        self.close_calls = 0

    def on_any(self, handler) -> None:
        self.registration_calls += 1
        if self.registration_error is not None:
            raise self.registration_error
        self.handler = handler

    async def start(self) -> None:
        self.start_calls += 1
        if self.start_error is not None:
            raise self.start_error
        if self.event is not None and self.handler is not None:
            self.handler(self.event)
        if self.block:
            await _block_forever()

    async def close(self) -> None:
        self.close_calls += 1
        if self.close_error is not None:
            raise self.close_error

    def err(self):
        return self.stream_error


class FakeSDKClient:
    def __init__(
        self,
        stream: FakeStream | None = None,
        *,
        open_error: Exception | None = None,
    ) -> None:
        self.stream = stream or FakeStream()
        self.open_error = open_error
        self.open_calls = 0

    async def open_negotiation_stream(self):
        self.open_calls += 1
        if self.open_error is not None:
            raise self.open_error
        return self.stream


class FakeSDKLoader:
    def __init__(
        self,
        client: FakeSDKClient | None = None,
        *,
        load_error: Exception | None = None,
    ) -> None:
        self.client = client or FakeSDKClient()
        self.load_error = load_error
        self.calls = 0

    def __call__(self):
        self.calls += 1
        if self.load_error is not None:
            raise self.load_error
        return self.client


class RecordingRunner:
    def __init__(self) -> None:
        self.delegate = OptionBNegotiationPilotRunner()
        self.events = []

    def prepare(self, request, *, run_registry=None):
        return self.delegate.prepare(request, run_registry=run_registry)

    async def simulate_negotiation(self, request, *, event, run_registry=None):
        self.events.append(dict(event))
        return await self.delegate.simulate_negotiation(
            request,
            event=event,
            run_registry=run_registry,
        )


async def _block_forever() -> None:
    import asyncio

    await asyncio.Event().wait()


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


def ready_gates(**overrides) -> PilotGateSnapshot:
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
        "runtime_timeout_seconds": 0.05,
        "close_timeout_seconds": 0.05,
        "max_events": 1,
    }
    values.update(overrides)
    return PilotGateSnapshot(**values)


def pilot_request(**overrides) -> OptionBNegotiationPilotRequest:
    readiness_values = {
        "option": "option_b",
        "git_status_clean": True,
        "dashboard": ready_dashboard(),
        "gates": ready_gates(),
        "run_id": "pilot-2026-06-30-option-b2b-001",
        "approval_granted": True,
        "approval_token_present": True,
    }
    readiness_values.update(overrides.pop("readiness_overrides", {}))
    values = {
        "readiness": PilotReadinessRequest(**readiness_values),
        "connector_start_authorized": True,
        "requester_kill_switch_enabled": True,
    }
    values.update(overrides)
    return OptionBNegotiationPilotRequest(**values)


def connector_request(**overrides) -> QuarantinedConnectorRequest:
    values = {
        "pilot": pilot_request(),
        "sdk_load_authorized": True,
    }
    values.update(overrides)
    return QuarantinedConnectorRequest(**values)


def negotiation_event(**overrides):
    values = {
        "type": "order_negotiation_created",
        "negotiation_id": "raw-negotiation-id",
        "service_id": "wrong-service",
        "service_name": "Untrusted",
        "requirements_type": "schema",
        "requirements": {},
    }
    values.update(overrides)
    return values


def test_import_and_construction_do_not_load_sdk_or_start_stream() -> None:
    loader = FakeSDKLoader()

    QuarantinedSDKNegotiationConnector(sdk_loader=loader)

    assert loader.calls == 0
    assert loader.client.open_calls == 0
    assert loader.client.stream.start_calls == 0


@pytest.mark.anyio
async def test_default_request_blocks_before_sdk_load() -> None:
    loader = FakeSDKLoader()
    connector = QuarantinedSDKNegotiationConnector(sdk_loader=loader)

    result = await connector.run(QuarantinedConnectorRequest())

    assert result.status == "no_go"
    assert result.sdk_load_attempted is False
    assert result.stream_start_attempted is False
    assert result.live_execution_authorized is False
    assert result.mutating_methods_called is False
    assert result.real_cap_ready is False
    assert loader.calls == 0


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("connector_input", "reason"),
    [
        (
            connector_request(
                pilot=pilot_request(connector_start_authorized=False)
            ),
            "connector_start_not_authorized",
        ),
        (
            connector_request(
                pilot=pilot_request(
                    readiness_overrides={
                        "gates": ready_gates(cap_pilot_enabled=False)
                    }
                )
            ),
            "master_pilot_gate_disabled",
        ),
        (
            connector_request(sdk_load_authorized=False),
            "sdk_load_not_authorized",
        ),
    ],
)
async def test_required_gates_block_before_sdk_load(connector_input, reason) -> None:
    loader = FakeSDKLoader()

    result = await QuarantinedSDKNegotiationConnector(
        sdk_loader=loader
    ).run(connector_input, run_registry=FakeRunRegistry())

    assert result.status == "no_go"
    assert reason in result.reason_codes
    assert result.sdk_load_attempted is False
    assert loader.calls == 0


@pytest.mark.anyio
async def test_negotiation_event_routes_to_option_b_manual_review() -> None:
    stream = FakeStream(event=negotiation_event())
    client = FakeSDKClient(stream)
    loader = FakeSDKLoader(client)

    result = await QuarantinedSDKNegotiationConnector(
        sdk_loader=loader
    ).run(connector_request(), run_registry=FakeRunRegistry())

    assert result.status == "manual_review"
    assert result.runner_result is not None
    assert result.runner_result.status == "manual_review_simulated"
    assert result.runner_result.directive_action == "would_manual_review"
    assert result.sdk_load_attempted is True
    assert result.sdk_loaded is True
    assert result.stream_start_attempted is True
    assert result.event_received is True
    assert result.close_attempted is True
    assert result.closed is True
    assert stream.registration_calls == 1
    assert stream.start_calls == 1
    assert stream.close_calls == 1


@pytest.mark.anyio
@pytest.mark.parametrize(
    "event",
    [
        {"type": "order_paid"},
        {"type": "paid_order"},
        {"type": "order_delivered"},
        {"type": "order_settled"},
        {"type": "unknown_event"},
        {"type": 123},
        {},
    ],
)
async def test_non_negotiation_events_fail_closed(event) -> None:
    stream = FakeStream(event=event)

    result = await QuarantinedSDKNegotiationConnector(
        sdk_loader=FakeSDKLoader(FakeSDKClient(stream))
    ).run(connector_request(), run_registry=FakeRunRegistry())

    assert result.status == "no_go"
    assert result.reason_codes == ["unsupported_event_type"]
    assert result.runner_result is None
    assert result.mutating_methods_called is False
    assert result.closed is True
    assert stream.close_calls == 1


@pytest.mark.anyio
async def test_event_is_allowlisted_and_evidence_is_sanitized() -> None:
    raw_event = negotiation_event(
        negotiation_id="raw-event-id",
        callback_url="wss://user:secret@example.test/ws?token=raw-token",
        authorization="Bearer raw-header-secret",
        sdk_key="croo_sk_raw-key",
        requirements={
            "token": "croo_sk_token-secret",
            "chain": "ethereum",
            "intended_action": "evaluate",
            "size_usd": 1,
        },
    )
    stream = FakeStream(event=raw_event)
    runner = RecordingRunner()

    result = await QuarantinedSDKNegotiationConnector(
        sdk_loader=FakeSDKLoader(FakeSDKClient(stream)),
        runner=runner,
    ).run(connector_request(), run_registry=FakeRunRegistry())

    assert len(runner.events) == 1
    captured = runner.events[0]
    assert captured["type"] == "order_negotiation_created"
    assert "negotiation_id" not in captured
    assert "callback_url" not in captured
    assert "authorization" not in captured
    assert "sdk_key" not in captured
    assert captured["requirements"]["token"] == "[REDACTED]"
    evidence = result.model_dump_json()
    for secret in (
        "raw-event-id",
        "raw-token",
        "raw-header-secret",
        "croo_sk_raw-key",
        "croo_sk_token-secret",
        "wss://",
    ):
        assert secret not in evidence


@pytest.mark.anyio
async def test_timeout_closes_stream_once() -> None:
    stream = FakeStream(block=True)
    request = connector_request(
        pilot=pilot_request(
            readiness_overrides={
                "gates": ready_gates(runtime_timeout_seconds=0.01)
            }
        )
    )

    result = await QuarantinedSDKNegotiationConnector(
        sdk_loader=FakeSDKLoader(FakeSDKClient(stream))
    ).run(request, run_registry=FakeRunRegistry())

    assert result.status == "timed_out"
    assert result.closed is True
    assert stream.close_calls == 1


@pytest.mark.anyio
async def test_stream_error_is_sanitized_and_closes_once() -> None:
    stream = FakeStream(
        event=negotiation_event(),
        stream_error=RuntimeError(
            "wss://user:secret@example/ws?token=raw croo_sk_stream-secret"
        ),
    )

    result = await QuarantinedSDKNegotiationConnector(
        sdk_loader=FakeSDKLoader(FakeSDKClient(stream))
    ).run(connector_request(), run_registry=FakeRunRegistry())

    assert result.status == "stream_error"
    assert "croo_sk_stream-secret" not in (result.error or "")
    assert "wss://" not in (result.error or "")
    assert result.closed is True
    assert stream.close_calls == 1


@pytest.mark.anyio
async def test_registration_failure_is_sanitized_and_closes_once() -> None:
    stream = FakeStream(
        registration_error=RuntimeError(
            "Authorization: Bearer raw-secret croo_sk_registration"
        )
    )

    result = await QuarantinedSDKNegotiationConnector(
        sdk_loader=FakeSDKLoader(FakeSDKClient(stream))
    ).run(connector_request(), run_registry=FakeRunRegistry())

    assert result.status == "registration_failed"
    assert "raw-secret" not in (result.error or "")
    assert "croo_sk_registration" not in (result.error or "")
    assert result.close_attempted is True
    assert result.closed is True
    assert stream.close_calls == 1


@pytest.mark.anyio
async def test_start_failure_is_sanitized_and_closes_once() -> None:
    stream = FakeStream(
        start_error=RuntimeError("sdk_key=raw-start-secret")
    )

    result = await QuarantinedSDKNegotiationConnector(
        sdk_loader=FakeSDKLoader(FakeSDKClient(stream))
    ).run(connector_request(), run_registry=FakeRunRegistry())

    assert result.status == "stream_error"
    assert "raw-start-secret" not in (result.error or "")
    assert result.closed is True
    assert stream.close_calls == 1


@pytest.mark.anyio
async def test_close_failure_is_sanitized_and_attempted_once() -> None:
    stream = FakeStream(
        event=negotiation_event(),
        close_error=RuntimeError("api_key=raw-close-secret"),
    )

    result = await QuarantinedSDKNegotiationConnector(
        sdk_loader=FakeSDKLoader(FakeSDKClient(stream))
    ).run(connector_request(), run_registry=FakeRunRegistry())

    assert result.status == "close_failed"
    assert "raw-close-secret" not in (result.error or "")
    assert result.close_attempted is True
    assert result.closed is False
    assert stream.close_calls == 1


@pytest.mark.anyio
async def test_loader_failure_is_lazy_and_sanitized() -> None:
    loader = FakeSDKLoader(
        load_error=RuntimeError(
            "wss://user:secret@example/ws?token=raw croo_sk_loader-secret"
        )
    )

    result = await QuarantinedSDKNegotiationConnector(
        sdk_loader=loader
    ).run(connector_request(), run_registry=FakeRunRegistry())

    assert result.status == "setup_failed"
    assert result.sdk_load_attempted is True
    assert result.sdk_loaded is False
    assert "croo_sk_loader-secret" not in (result.error or "")
    assert "wss://" not in (result.error or "")


def test_connector_has_no_sdk_network_startup_or_mutating_imports() -> None:
    module_path = Path(
        "src/aegis_croo/cap/quarantined_sdk_connector.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    forbidden_imports = {
        "croo",
        "websocket",
        "websockets",
        "requests",
        "httpx",
        "aiohttp",
        "subprocess",
        "importlib",
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
        "run_forever",
        "start_server",
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


def test_application_paths_do_not_reference_quarantined_connector() -> None:
    module_name = "quarantined_sdk_connector"
    references = []
    for path in Path("src/aegis_croo").rglob("*.py"):
        if path.name == "quarantined_sdk_connector.py":
            continue
        if module_name in path.read_text(encoding="utf-8"):
            references.append(path)

    assert references == []
