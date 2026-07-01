import ast
import asyncio
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.aegis_croo.cap.gated_real_sdk_adapter import (
    RealCROOSDKCredentials,
    RealSDKGateSnapshot,
)
from src.aegis_croo.cap.manual_negotiation_pilot_runner import (
    ManualNegotiationPilotRequest,
    ManualRealNegotiationPilotRunner,
)
from src.aegis_croo.cap.option_b_pilot_runner import (
    OptionBNegotiationPilotRequest,
)
from src.aegis_croo.cap.pilot_readiness import (
    PilotGateSnapshot,
    PilotReadinessRequest,
    SanitizedDashboardStatus,
)


class FakeRunRegistry:
    def contains(self, _run_id: str) -> bool:
        return False


class FakeSDKEvent:
    def __init__(self, event_type: object, raw: dict | None = None) -> None:
        self.type = event_type
        self.raw = dict(raw or {})
        self.negotiation_id = "raw-event-id"


class FakeSDKEventStream:
    def __init__(
        self,
        *,
        events: list[FakeSDKEvent] | None = None,
        registration_error: Exception | None = None,
    ) -> None:
        self.events = list(events or [])
        self.registration_error = registration_error
        self.registration_calls = 0
        self.close_calls = 0

    def on_any(self, handler) -> None:
        self.registration_calls += 1
        if self.registration_error is not None:
            raise self.registration_error
        for event in self.events:
            handler(event)

    async def close(self) -> None:
        self.close_calls += 1

    def err(self):
        return None


class ScheduledSecondEventStream(FakeSDKEventStream):
    def __init__(self, schedule: str) -> None:
        super().__init__()
        self.schedule = schedule

    def on_any(self, handler) -> None:
        self.registration_calls += 1
        loop = asyncio.get_running_loop()
        first = negotiation_event()
        second = negotiation_event()
        if self.schedule == "queued":
            loop.call_soon(handler, first)
            loop.call_soon(handler, second)
            return
        handler(first)
        if self.schedule == "adjacent":
            loop.call_soon(handler, second)
        elif self.schedule == "timer_zero":
            loop.call_later(0, handler, second)
        elif self.schedule == "delayed":
            loop.call_later(0.01, handler, second)
        else:
            raise AssertionError(f"unsupported fake schedule: {self.schedule}")


class FakeSDKState:
    def __init__(
        self,
        *,
        stream: FakeSDKEventStream | None = None,
        block_connect: bool = False,
    ) -> None:
        self.stream = stream or FakeSDKEventStream()
        self.block_connect = block_connect
        self.import_calls: list[str] = []
        self.credentials_calls = 0
        self.client_calls = 0
        self.connect_calls = 0
        self.client_close_calls = 0

    def importer(self, name: str):
        self.import_calls.append(name)
        state = self

        class Config:
            def __init__(self, *, base_url: str, ws_url: str) -> None:
                self.base_url = base_url
                self.ws_url = ws_url

        class AgentClient:
            def __init__(self, _config, _sdk_key: str) -> None:
                state.client_calls += 1

            async def connect_websocket(self):
                state.connect_calls += 1
                if state.block_connect:
                    await asyncio.Event().wait()
                return state.stream

            async def close(self) -> None:
                state.client_close_calls += 1

        return SimpleNamespace(Config=Config, AgentClient=AgentClient)

    def credentials(self) -> RealCROOSDKCredentials:
        self.credentials_calls += 1
        return RealCROOSDKCredentials(
            api_url="https://api.example.test",
            ws_url="wss://ws.example.test/events",
            sdk_key="fake-sdk-key",
            service_id="fake-service-id",
            provider_agent_id="fake-provider-id",
        )


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
            run_id="pilot-b3a-fake-001",
            approval_granted=True,
            approval_token_present=True,
        ),
        connector_start_authorized=True,
        requester_kill_switch_enabled=True,
    )


def ready_sdk_gates(**overrides) -> RealSDKGateSnapshot:
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


def ready_request(**overrides) -> ManualNegotiationPilotRequest:
    values = {
        "pilot": ready_pilot_request(),
        "sdk_gates": ready_sdk_gates(),
        "manual_operator_approval": True,
        "max_events": 1,
    }
    values.update(overrides)
    return ManualNegotiationPilotRequest(**values)


def build_runner(state: FakeSDKState):
    return ManualRealNegotiationPilotRunner(
        credentials_provider=state.credentials,
        importer=state.importer,
    )


def negotiation_event(**raw_overrides) -> FakeSDKEvent:
    raw = {
        "service_id": "fake-service-id",
        "requirements_type": "schema",
        "requirements": {},
        "negotiation_id": "raw-event-id",
    }
    raw.update(raw_overrides)
    return FakeSDKEvent("order_negotiation_created", raw)


def test_import_and_construction_start_nothing() -> None:
    state = FakeSDKState()

    runner = build_runner(state)

    assert runner is not None
    assert state.import_calls == []
    assert state.credentials_calls == 0
    assert state.connect_calls == 0


@pytest.mark.anyio
async def test_default_request_blocks_before_sdk_loading() -> None:
    state = FakeSDKState()

    result = await build_runner(state).run_once(ManualNegotiationPilotRequest())

    assert result.status == "no_go"
    assert "manual_operator_approval_required" in result.reason_codes
    assert state.import_calls == []
    assert result.live_execution_authorized is False
    assert result.mutating_methods_called is False
    assert result.real_cap_ready is False


@pytest.mark.anyio
async def test_cap_mode_real_alone_blocks_before_sdk_loading() -> None:
    state = FakeSDKState()
    request = ManualNegotiationPilotRequest(
        sdk_gates=RealSDKGateSnapshot(cap_mode="real")
    )

    result = await build_runner(state).run_once(request)

    assert result.status == "no_go"
    assert "master_pilot_gate_disabled" in result.reason_codes
    assert "connector_start_not_authorized" in result.reason_codes
    assert "sdk_load_not_authorized" in result.reason_codes
    assert "option_b_pilot_not_authorized" in result.reason_codes
    assert state.import_calls == []


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("gate_name", "reason"),
    [
        ("cap_pilot_enabled", "master_pilot_gate_disabled"),
        ("connector_start_authorized", "connector_start_not_authorized"),
        ("sdk_load_authorized", "sdk_load_not_authorized"),
        (
            "option_b_negotiation_pilot_authorized",
            "option_b_pilot_not_authorized",
        ),
    ],
)
async def test_missing_required_gate_blocks_before_sdk_loading(
    gate_name: str,
    reason: str,
) -> None:
    state = FakeSDKState()
    request = ready_request(sdk_gates=ready_sdk_gates(**{gate_name: False}))

    result = await build_runner(state).run_once(
        request,
        run_registry=FakeRunRegistry(),
    )

    assert result.status == "no_go"
    assert reason in result.reason_codes
    assert state.import_calls == []


@pytest.mark.anyio
async def test_manual_operator_approval_false_blocks() -> None:
    state = FakeSDKState()

    result = await build_runner(state).run_once(
        ready_request(manual_operator_approval=False),
        run_registry=FakeRunRegistry(),
    )

    assert result.status == "no_go"
    assert result.reason_codes == ["manual_operator_approval_required"]
    assert state.import_calls == []


@pytest.mark.anyio
async def test_max_events_must_equal_one() -> None:
    state = FakeSDKState()

    result = await build_runner(state).run_once(
        ready_request(max_events=2),
        run_registry=FakeRunRegistry(),
    )

    assert result.status == "no_go"
    assert result.reason_codes == ["event_limit_invalid"]
    assert state.import_calls == []


@pytest.mark.anyio
async def test_fund_transfer_enabled_blocks() -> None:
    state = FakeSDKState()

    result = await build_runner(state).run_once(
        ready_request(sdk_gates=ready_sdk_gates(require_fund_transfer=True)),
        run_registry=FakeRunRegistry(),
    )

    assert result.status == "no_go"
    assert result.reason_codes == ["fund_transfer_enabled"]
    assert state.import_calls == []


@pytest.mark.anyio
async def test_one_negotiation_event_returns_sanitized_manual_review() -> None:
    event = negotiation_event(
        authorization="Bearer fake-secret",
        callback_url="wss://user:pass@example.test/ws?key=fake-secret",
    )
    state = FakeSDKState(stream=FakeSDKEventStream(events=[event]))

    result = await build_runner(state).run_once(
        ready_request(),
        run_registry=FakeRunRegistry(),
    )

    assert result.status == "manual_review"
    assert result.negotiation_evidence is not None
    assert result.close_attempted is True
    assert result.closed is True
    assert state.connect_calls == 1
    assert state.stream.close_calls == 1
    assert state.client_close_calls == 1
    assert result.live_execution_authorized is False
    assert result.mutating_methods_called is False
    assert result.real_cap_ready is False
    serialized = result.model_dump_json()
    assert "raw-event-id" not in serialized
    assert "fake-secret" not in serialized
    assert "wss://" not in serialized


@pytest.mark.anyio
@pytest.mark.parametrize(
    "event_type",
    ["order_paid", "order_delivered", "order_settled", "unknown", "", None],
)
async def test_non_negotiation_events_fail_closed(event_type: object) -> None:
    state = FakeSDKState(
        stream=FakeSDKEventStream(events=[FakeSDKEvent(event_type)])
    )

    result = await build_runner(state).run_once(
        ready_request(),
        run_registry=FakeRunRegistry(),
    )

    assert result.status == "no_go"
    assert result.reason_codes == ["unsupported_event_type"]
    assert result.negotiation_evidence is None
    assert result.closed is True


@pytest.mark.anyio
async def test_duplicate_events_fail_closed() -> None:
    state = FakeSDKState(
        stream=FakeSDKEventStream(
            events=[negotiation_event(), negotiation_event()]
        )
    )

    result = await build_runner(state).run_once(
        ready_request(),
        run_registry=FakeRunRegistry(),
    )

    assert result.status == "no_go"
    assert result.reason_codes == ["multiple_events_observed"]
    assert result.negotiation_evidence is None
    assert state.stream.close_calls == 1
    assert state.client_close_calls == 1


@pytest.mark.anyio
async def test_adjacent_turn_second_event_fails_closed_and_closes_once() -> None:
    state = FakeSDKState(stream=ScheduledSecondEventStream("adjacent"))

    result = await build_runner(state).run_once(
        ready_request(),
        run_registry=FakeRunRegistry(),
    )

    assert result.status == "no_go"
    assert result.status != "manual_review"
    assert result.reason_codes == ["multiple_events_observed"]
    assert result.negotiation_evidence is None
    assert result.close_attempted is True
    assert result.closed is True
    assert state.stream.close_calls == 1
    assert state.client_close_calls == 1


@pytest.mark.anyio
@pytest.mark.parametrize("schedule", ["queued", "timer_zero", "delayed"])
async def test_queued_and_deferred_second_events_fail_closed(
    schedule: str,
) -> None:
    state = FakeSDKState(stream=ScheduledSecondEventStream(schedule))

    result = await build_runner(state).run_once(
        ready_request(),
        run_registry=FakeRunRegistry(),
    )

    assert result.status == "no_go"
    assert result.reason_codes == ["multiple_events_observed"]
    assert result.negotiation_evidence is None
    assert result.close_attempted is True
    assert result.closed is True
    assert state.stream.close_calls == 1
    assert state.client_close_calls == 1


@pytest.mark.anyio
async def test_registration_failure_closes_once_with_sanitized_error() -> None:
    state = FakeSDKState(
        stream=FakeSDKEventStream(
            registration_error=RuntimeError(
                "Authorization: fake-secret wss://example.test?key=fake-secret"
            )
        )
    )

    result = await build_runner(state).run_once(
        ready_request(),
        run_registry=FakeRunRegistry(),
    )

    assert result.status == "stream_error"
    assert result.error == "sdk_stream_registration_failed"
    assert result.close_attempted is True
    assert result.closed is True
    assert state.stream.close_calls == 1
    assert state.client_close_calls == 1
    assert "fake-secret" not in result.model_dump_json()


@pytest.mark.anyio
async def test_timeout_closes_once() -> None:
    state = FakeSDKState(block_connect=True)

    result = await build_runner(state).run_once(
        ready_request(),
        run_registry=FakeRunRegistry(),
    )

    assert result.status == "timed_out"
    assert result.reason_codes == ["event_timeout"]
    assert result.close_attempted is True
    assert result.closed is True
    assert state.client_close_calls == 1


@pytest.mark.anyio
async def test_all_secret_surfaces_are_absent_from_evidence() -> None:
    event = negotiation_event(
        service_id="service-secret",
        headers={"X-API-Key": "header-secret"},
        url="wss://user:pass@example/ws?key=query-secret",
        api_key="api-secret",
        nested={"secret": "nested-secret"},
    )
    state = FakeSDKState(stream=FakeSDKEventStream(events=[event]))

    result = await build_runner(state).run_once(
        ready_request(),
        run_registry=FakeRunRegistry(),
    )

    serialized = result.model_dump_json()
    for secret in (
        "service-secret",
        "header-secret",
        "query-secret",
        "api-secret",
        "nested-secret",
        "raw-event-id",
        "wss://",
    ):
        assert secret not in serialized


def test_manual_runner_has_no_forbidden_imports_or_lifecycle_calls() -> None:
    path = Path("src/aegis_croo/cap/manual_negotiation_pilot_runner.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden_imports = {
        "croo",
        "requests",
        "httpx",
        "aiohttp",
        "websocket",
        "websockets",
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
        "settle_order",
        "clear_order",
        "wallet",
        "sign",
        "swap",
        "broadcast",
        "trade",
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


def test_application_paths_do_not_reference_manual_runner() -> None:
    references = []
    for root in (Path("apps"), Path("src/aegis_croo")):
        for path in root.rglob("*.py"):
            if path.name == "manual_negotiation_pilot_runner.py":
                continue
            if "manual_negotiation_pilot_runner" in path.read_text(
                encoding="utf-8"
            ):
                references.append(path)

    assert references == []
