import ast
from decimal import Decimal
from pathlib import Path

import pytest

from src.aegis_croo.cap.pilot_readiness import (
    DuplicatePilotRunIDError,
    FakePilotActionAdapter,
    PilotApprovalRequiredError,
    PilotGateSnapshot,
    PilotReadinessRequest,
    PilotRunLockRegistry,
    SanitizedDashboardStatus,
    SanitizedPilotEvidence,
    evaluate_pilot_readiness,
)


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


def ready_request(
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
        "run_id": "pilot-2026-06-30-option-b-001",
        "approval_granted": True,
        "approval_token_present": True,
    }
    values.update(overrides)
    return PilotReadinessRequest(**values)


def test_default_state_is_no_go() -> None:
    result = evaluate_pilot_readiness(PilotReadinessRequest())

    assert result.status == "no_go"
    assert result.approval_ready is False
    assert result.local_only is True
    assert result.real_action_performed is False
    assert result.real_cap_ready is False
    assert result.reason_codes


@pytest.mark.parametrize(
    "field",
    [
        "profile_complete",
        "service_identity_verified",
        "requirements_schema_verified",
        "deliverable_schema_verified",
    ],
)
def test_missing_dashboard_checks_stay_no_go(field: str) -> None:
    result = evaluate_pilot_readiness(
        ready_request(dashboard=ready_dashboard(**{field: False}))
    )

    assert result.status == "no_go"
    assert "dashboard_check_failed" in result.reason_codes


def test_require_fund_transfer_on_is_no_go() -> None:
    result = evaluate_pilot_readiness(
        ready_request(dashboard=ready_dashboard(require_fund_transfer=True))
    )

    assert result.status == "no_go"
    assert "fund_transfer_enabled" in result.reason_codes


def test_wrong_price_is_no_go() -> None:
    result = evaluate_pilot_readiness(
        ready_request(
            dashboard=ready_dashboard(service_price_usdc=Decimal("0.25"))
        )
    )

    assert result.status == "no_go"
    assert "wrong_service_price" in result.reason_codes


def test_pending_orders_or_negotiations_is_no_go() -> None:
    result = evaluate_pilot_readiness(
        ready_request(
            dashboard=ready_dashboard(no_pending_negotiations_or_orders=False)
        )
    )

    assert result.status == "no_go"
    assert "pending_negotiations_or_orders" in result.reason_codes


def test_missing_idempotency_run_id_is_no_go() -> None:
    result = evaluate_pilot_readiness(ready_request(run_id=None))

    assert result.status == "no_go"
    assert "missing_run_id" in result.reason_codes


def test_duplicate_run_id_is_no_go() -> None:
    registry = PilotRunLockRegistry()
    evidence = SanitizedPilotEvidence(
        run_id="pilot-2026-06-30-option-b-001",
        option="option_b",
        readiness_status="approval_ready",
        reason_codes=[],
    )
    registry.reserve(
        run_id=evidence.run_id,
        option="option_b",
        approval_granted=True,
        approval_token_present=True,
        evidence=evidence,
    )

    result = evaluate_pilot_readiness(
        ready_request(),
        run_registry=registry,
    )

    assert result.status == "no_go"
    assert "duplicate_run_id" in result.reason_codes


def test_missing_requester_kill_switch_is_no_go() -> None:
    result = evaluate_pilot_readiness(
        ready_request(gates=ready_option_b_gates(requester_enabled=False))
    )

    assert result.status == "no_go"
    assert "requester_gate_disabled" in result.reason_codes



def test_missing_master_pilot_gate_defaults_false_and_is_no_go() -> None:
    gate_values = ready_option_b_gates().model_dump()
    gate_values.pop("cap_pilot_enabled", None)
    gates = PilotGateSnapshot(**gate_values)

    result = evaluate_pilot_readiness(
        ready_request(gates=gates),
        run_registry=PilotRunLockRegistry(),
    )

    assert getattr(gates, "cap_pilot_enabled", None) is False
    assert result.status == "no_go"
    assert "master_pilot_gate_disabled" in result.reason_codes


def test_false_master_pilot_gate_is_no_go() -> None:
    result = evaluate_pilot_readiness(
        ready_request(
            gates=ready_option_b_gates(cap_pilot_enabled=False),
        ),
        run_registry=PilotRunLockRegistry(),
    )

    assert result.status == "no_go"
    assert "master_pilot_gate_disabled" in result.reason_codes

def test_required_gates_must_be_explicit_and_bounded() -> None:
    result = evaluate_pilot_readiness(
        ready_request(
            gates=ready_option_b_gates(
                no_retry=None,
                runtime_timeout_seconds=61.0,
                close_timeout_seconds=0.0,
                max_events=0,
            )
        )
    )

    assert result.status == "no_go"
    assert "required_gate_not_explicit" in result.reason_codes
    assert "runtime_timeout_unbounded" in result.reason_codes
    assert "close_timeout_unbounded" in result.reason_codes
    assert "event_limit_invalid" in result.reason_codes


def test_all_prerequisites_return_approval_ready_for_option_b_only() -> None:
    result = evaluate_pilot_readiness(
        ready_request(),
        run_registry=PilotRunLockRegistry(),
    )

    assert result.status == "approval_ready"
    assert result.option == "option_b"
    assert result.approval_ready is True
    assert result.live_execution_authorized is False
    assert result.reason_codes == []
    assert result.real_action_performed is False
    assert result.real_cap_ready is False


def test_missing_run_registry_is_no_go() -> None:
    result = evaluate_pilot_readiness(ready_request())

    assert result.status == "no_go"
    assert result.approval_ready is False
    assert "run_registry_unavailable" in result.reason_codes


def test_unavailable_run_registry_is_no_go() -> None:
    class UnavailableRunRegistry:
        def contains(self, run_id: str) -> bool:
            raise RuntimeError("registry unavailable")

    result = evaluate_pilot_readiness(
        ready_request(),
        run_registry=UnavailableRunRegistry(),
    )

    assert result.status == "no_go"
    assert result.approval_ready is False
    assert "run_registry_unavailable" in result.reason_codes


def test_option_c_remains_separate_approval_required() -> None:
    option_c_gates = ready_option_b_gates(
        pay_enabled=True,
        accept_enabled=True,
        paid_order_handling_enabled=True,
        deliver_enabled=True,
        max_events=3,
    )

    result = evaluate_pilot_readiness(
        ready_request(
            option="option_c",
            gates=option_c_gates,
            run_id="pilot-2026-06-30-option-c-001",
        ),
        run_registry=PilotRunLockRegistry(),
    )

    assert result.status == "separate_approval_required"
    assert result.option == "option_c"
    assert result.approval_ready is False
    assert result.reason_codes == ["option_c_future_step_required"]
    assert result.real_cap_ready is False


def test_run_lock_requires_explicit_approval_and_stores_sanitized_evidence() -> None:
    registry = PilotRunLockRegistry()
    evidence = SanitizedPilotEvidence(
        run_id="pilot-safe-001",
        option="option_b",
        readiness_status="approval_ready",
        reason_codes=[],
    )

    with pytest.raises(PilotApprovalRequiredError):
        registry.reserve(
            run_id=evidence.run_id,
            option="option_b",
            approval_granted=False,
            approval_token_present=False,
            evidence=evidence,
        )

    lock = registry.reserve(
        run_id=evidence.run_id,
        option="option_b",
        approval_granted=True,
        approval_token_present=True,
        evidence=evidence,
    )

    assert lock.approval_granted is True
    assert lock.approval_token_present is True
    assert lock.evidence == evidence
    assert set(lock.model_dump()) == {
        "run_id",
        "option",
        "approval_granted",
        "approval_token_present",
        "evidence",
    }
    assert registry.get(evidence.run_id) == lock
    with pytest.raises(DuplicatePilotRunIDError):
        registry.reserve(
            run_id=evidence.run_id,
            option="option_b",
            approval_granted=True,
            approval_token_present=True,
            evidence=evidence,
        )


def test_fake_action_adapter_records_would_directives_only() -> None:
    adapter = FakePilotActionAdapter()

    adapter.record("would_receive_negotiation", ["valid_aegis_risk_check"])
    adapter.record("would_manual_review", ["provider_mutations_disabled"])
    directives = adapter.directives()

    assert [item.action for item in directives] == [
        "would_receive_negotiation",
        "would_manual_review",
    ]
    assert all(item.local_only is True for item in directives)
    assert all(item.real_action_performed is False for item in directives)
    directives.clear()
    assert len(adapter.directives()) == 2


def test_pilot_readiness_module_has_no_sdk_network_or_mutating_calls() -> None:
    module_path = Path("src/aegis_croo/cap/pilot_readiness.py")
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
        if isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name))
    }

    assert forbidden_imports.isdisjoint(imported_roots)
    assert forbidden_calls.isdisjoint(called_names)
