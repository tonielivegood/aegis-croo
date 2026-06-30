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


class FakeRunRegistry:
    def __init__(self, *, contains: bool = False) -> None:
        self._contains = contains

    def contains(self, _run_id: str) -> bool:
        return self._contains


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
        "runtime_timeout_seconds": 5.0,
        "close_timeout_seconds": 1.0,
        "max_events": 1,
    }
    values.update(overrides)
    return PilotGateSnapshot(**values)


def ready_request(**overrides) -> OptionBNegotiationPilotRequest:
    readiness_values = {
        "option": "option_b",
        "git_status_clean": True,
        "dashboard": ready_dashboard(),
        "gates": ready_gates(),
        "run_id": "pilot-2026-06-30-option-b2a-001",
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


def test_default_runner_state_is_no_go_and_never_connects() -> None:
    result = OptionBNegotiationPilotRunner().prepare(
        OptionBNegotiationPilotRequest()
    )

    assert result.status == "no_go"
    assert result.connection_plan is None
    assert result.connection_attempted is False
    assert result.provider_listener_started is False
    assert result.live_execution_authorized is False
    assert result.mutating_methods_called is False
    assert result.real_cap_ready is False


@pytest.mark.parametrize(
    ("pilot_request", "registry", "reason"),
    [
        (
            ready_request(
                readiness_overrides={
                    "gates": ready_gates(cap_pilot_enabled=False)
                }
            ),
            FakeRunRegistry(),
            "master_pilot_gate_disabled",
        ),
        (
            ready_request(connector_start_authorized=False),
            FakeRunRegistry(),
            "connector_start_not_authorized",
        ),
        (
            ready_request(requester_kill_switch_enabled=False),
            FakeRunRegistry(),
            "requester_kill_switch_disabled",
        ),
        (
            ready_request(readiness_overrides={"run_id": None}),
            FakeRunRegistry(),
            "missing_run_id",
        ),
        (ready_request(), None, "run_registry_unavailable"),
        (ready_request(), FakeRunRegistry(contains=True), "duplicate_run_id"),
        (
            ready_request(
                readiness_overrides={"dashboard": SanitizedDashboardStatus()}
            ),
            FakeRunRegistry(),
            "dashboard_check_failed",
        ),
        (
            ready_request(
                readiness_overrides={
                    "dashboard": ready_dashboard(
                        no_pending_negotiations_or_orders=False
                    )
                }
            ),
            FakeRunRegistry(),
            "pending_negotiations_or_orders",
        ),
        (
            ready_request(
                readiness_overrides={
                    "gates": ready_gates(runtime_timeout_seconds=6.0)
                }
            ),
            FakeRunRegistry(),
            "runtime_timeout_unbounded",
        ),
        (
            ready_request(
                readiness_overrides={
                    "gates": ready_gates(close_timeout_seconds=2.0)
                }
            ),
            FakeRunRegistry(),
            "close_timeout_unbounded",
        ),
        (
            ready_request(
                readiness_overrides={"gates": ready_gates(max_events=2)}
            ),
            FakeRunRegistry(),
            "event_limit_invalid",
        ),
    ],
)
def test_incomplete_or_unsafe_prerequisites_are_no_go(
    pilot_request, registry, reason
) -> None:
    result = OptionBNegotiationPilotRunner().prepare(
        pilot_request,
        run_registry=registry,
    )

    assert result.status == "no_go"
    assert reason in result.reason_codes
    assert result.connection_plan is None
    assert result.connection_attempted is False


def test_complete_facts_produce_manual_review_plan_without_execution() -> None:
    result = OptionBNegotiationPilotRunner().prepare(
        ready_request(),
        run_registry=FakeRunRegistry(),
    )

    assert result.status == "manual_review_plan_ready"
    assert result.approval_ready is True
    assert result.connection_plan is not None
    assert result.connection_plan.directive == "manual_review_only"
    assert result.connection_plan.max_events == 1
    assert result.connection_plan.runtime_timeout_seconds == 5.0
    assert result.connection_plan.close_timeout_seconds == 1.0
    assert result.connection_attempted is False
    assert result.provider_listener_started is False
    assert result.live_execution_authorized is False
    assert result.mutating_methods_called is False
    assert result.real_cap_ready is False


def test_option_c_remains_separate_approval_required() -> None:
    request = ready_request(
        readiness_overrides={
            "option": "option_c",
            "gates": ready_gates(
                pay_enabled=True,
                accept_enabled=True,
                paid_order_handling_enabled=True,
                deliver_enabled=True,
                max_events=3,
            ),
        }
    )

    result = OptionBNegotiationPilotRunner().prepare(
        request,
        run_registry=FakeRunRegistry(),
    )

    assert result.status == "separate_approval_required"
    assert result.approval_ready is False
    assert result.connection_plan is None
    assert result.live_execution_authorized is False


@pytest.mark.anyio
async def test_simulated_negotiation_routes_to_manual_review_only() -> None:
    event = {
        "type": "order_negotiation_created",
        "negotiation_id": "raw-negotiation-id-should-not-leak",
        "service_id": "wrong-service",
        "service_name": "Untrusted",
        "requirements_type": "schema",
        "requirements": {},
        "callback_url": "wss://user:secret@example.test/ws?token=raw-secret",
        "authorization": "Bearer raw-secret",
    }

    result = await OptionBNegotiationPilotRunner().simulate_negotiation(
        ready_request(),
        event=event,
        run_registry=FakeRunRegistry(),
    )

    assert result.status == "manual_review_simulated"
    assert result.simulated_event is not None
    assert result.simulated_event.event_type == "order_negotiation_created"
    assert result.simulated_event.has_negotiation_id is True
    assert result.directive_action == "would_manual_review"
    assert result.closed is True
    assert result.connection_attempted is False
    assert result.provider_listener_started is False
    assert result.live_execution_authorized is False
    assert result.mutating_methods_called is False
    evidence = result.model_dump_json()
    assert "raw-negotiation-id-should-not-leak" not in evidence
    assert "raw-secret" not in evidence
    assert "wss://" not in evidence


def test_runner_has_no_sdk_network_start_or_mutating_calls() -> None:
    module_path = Path("src/aegis_croo/cap/option_b_pilot_runner.py")
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
