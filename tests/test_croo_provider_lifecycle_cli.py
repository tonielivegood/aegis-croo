import ast
from pathlib import Path

import pytest

from scripts.croo_provider_lifecycle import run_lifecycle


@pytest.mark.anyio
async def test_startup_without_explicit_enable_causes_no_connection(monkeypatch) -> None:
    monkeypatch.delenv("CAP_REAL_LIFECYCLE_ENABLED", raising=False)
    monkeypatch.delenv("CROO_WS_URL", raising=False)
    monkeypatch.delenv("CROO_SDK_KEY", raising=False)
    monkeypatch.delenv("CROO_SERVICE_ID", raising=False)
    monkeypatch.delenv("CROO_EXPECTED_REQUESTER_AGENT_ID", raising=False)

    # No CROO_WS_URL/CROO_SDK_KEY are set; if the top-level gate did not fail
    # closed first, constructing the SDK client would raise a KeyError
    # instead of this function returning cleanly.
    exit_code = await run_lifecycle()
    assert exit_code == 1


@pytest.mark.anyio
async def test_missing_allowlist_fails_closed_when_lifecycle_enabled(monkeypatch) -> None:
    monkeypatch.setenv("CAP_REAL_LIFECYCLE_ENABLED", "true")
    monkeypatch.delenv("CROO_SERVICE_ID", raising=False)
    monkeypatch.delenv("CROO_EXPECTED_REQUESTER_AGENT_ID", raising=False)
    monkeypatch.delenv("CROO_WS_URL", raising=False)
    monkeypatch.delenv("CROO_SDK_KEY", raising=False)

    exit_code = await run_lifecycle()
    assert exit_code == 1


@pytest.mark.anyio
async def test_missing_env_fails_closed_with_full_allowlist(monkeypatch) -> None:
    monkeypatch.setenv("CAP_REAL_LIFECYCLE_ENABLED", "true")
    monkeypatch.setenv("CROO_SERVICE_ID", "svc-real-123")
    monkeypatch.setenv("CROO_EXPECTED_REQUESTER_AGENT_ID", "req-agent-real-456")
    monkeypatch.delenv("CROO_WS_URL", raising=False)
    monkeypatch.delenv("CROO_SDK_KEY", raising=False)

    exit_code = await run_lifecycle()
    assert exit_code == 1


def test_cli_module_has_no_forbidden_mutating_calls() -> None:
    module_path = Path("scripts/croo_provider_lifecycle.py")
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    forbidden_calls = {
        "negotiate_order",
        "accept_negotiation_with_fund_address",
        "reject_negotiation",
        "pay_order",
        "reject_order",
        "upload_file",
        "settle_order",
        "clear_order",
    }
    called_names = {
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name))
    }
    assert forbidden_calls.isdisjoint(called_names)
