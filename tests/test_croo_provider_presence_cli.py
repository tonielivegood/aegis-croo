import ast
from pathlib import Path

import pytest

from scripts.croo_provider_presence import run_presence


@pytest.mark.anyio
async def test_startup_without_explicit_enable_causes_no_connection(monkeypatch) -> None:
    monkeypatch.delenv("CAP_PROVIDER_PRESENCE_ENABLED", raising=False)
    monkeypatch.delenv("CROO_WS_URL", raising=False)
    monkeypatch.delenv("CROO_SDK_KEY", raising=False)

    # No CROO_WS_URL/CROO_SDK_KEY are set; if the guard did not fail closed
    # first, constructing the SDK client would raise a KeyError instead of
    # this function returning cleanly.
    exit_code = await run_presence()
    assert exit_code == 1


@pytest.mark.anyio
async def test_missing_required_env_fails_closed_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("CAP_PROVIDER_PRESENCE_ENABLED", "true")
    monkeypatch.delenv("CROO_WS_URL", raising=False)
    monkeypatch.delenv("CROO_SDK_KEY", raising=False)

    exit_code = await run_presence()
    assert exit_code == 1


def test_cli_module_has_no_mutating_calls() -> None:
    module_path = Path("scripts/croo_provider_presence.py")
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
        "settle_order",
        "clear_order",
    }
    called_names = {
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name))
    }
    assert forbidden_calls.isdisjoint(called_names)
