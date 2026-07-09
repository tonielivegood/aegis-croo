import ast
from pathlib import Path

import pytest

import scripts.croo_requester_canary as requester_canary
from src.aegis_croo.cap.config import (
    configured_requester_canary_enabled,
    configured_requester_pay_enabled,
)


SAFE_BUY = {
    "token": "BNB",
    "chain": "bsc",
    "intended_action": "buy",
    "size_usd": 100,
}


def test_requester_canary_default_disabled(monkeypatch) -> None:
    monkeypatch.delenv("CAP_REQUESTER_CANARY_ENABLED", raising=False)
    assert configured_requester_canary_enabled() is False


def test_requester_pay_default_disabled(monkeypatch) -> None:
    monkeypatch.delenv("CAP_REQUESTER_PAY_ENABLED", raising=False)
    assert configured_requester_pay_enabled() is False


@pytest.mark.anyio
async def test_negotiate_unreachable_without_canary_flag(monkeypatch) -> None:
    monkeypatch.delenv("CAP_REQUESTER_CANARY_ENABLED", raising=False)
    monkeypatch.delenv("CROO_SERVICE_ID", raising=False)
    monkeypatch.delenv("CROO_REQUESTER_SDK_KEY", raising=False)

    with pytest.raises(RuntimeError, match="CAP_REQUESTER_CANARY_ENABLED"):
        await requester_canary.negotiate(SAFE_BUY)


@pytest.mark.anyio
async def test_pay_unreachable_without_independent_pay_flag(monkeypatch) -> None:
    monkeypatch.setenv("CAP_REQUESTER_CANARY_ENABLED", "true")
    monkeypatch.delenv("CAP_REQUESTER_PAY_ENABLED", raising=False)
    monkeypatch.delenv("CROO_REQUESTER_SDK_KEY", raising=False)

    with pytest.raises(RuntimeError, match="CAP_REQUESTER_PAY_ENABLED"):
        await requester_canary.pay("order-1")


@pytest.mark.anyio
async def test_provider_key_is_not_implicitly_reused(monkeypatch) -> None:
    monkeypatch.setenv("CAP_REQUESTER_CANARY_ENABLED", "true")
    monkeypatch.setenv("CROO_SERVICE_ID", "svc-real-123")
    monkeypatch.setenv("CROO_SDK_KEY", "croo_sk_provider-only-secret")
    monkeypatch.delenv("CROO_REQUESTER_SDK_KEY", raising=False)

    with pytest.raises(RuntimeError, match="CROO_REQUESTER_SDK_KEY"):
        await requester_canary.negotiate(SAFE_BUY)


@pytest.mark.anyio
async def test_negotiate_failure_is_redacted(monkeypatch) -> None:
    monkeypatch.setenv("CAP_REQUESTER_CANARY_ENABLED", "true")
    monkeypatch.setenv("CROO_SERVICE_ID", "svc-real-123")
    monkeypatch.setenv("CROO_REQUESTER_SDK_KEY", "croo_sk_requester-secret")

    class FakeClient:
        async def close(self) -> None:
            pass

    class FakeSDK:
        AgentClient = None
        Config = None

        @staticmethod
        def NegotiateOrderRequest(**kwargs):
            raise RuntimeError("failed key=croo_sk_requester-secret")

    monkeypatch.setattr(
        requester_canary, "_create_requester_client", lambda: FakeClient()
    )
    monkeypatch.setattr(requester_canary, "import_module", lambda _name: FakeSDK())

    with pytest.raises(RuntimeError) as exc_info:
        await requester_canary.negotiate(SAFE_BUY)

    assert "croo_sk_" not in str(exc_info.value)
    assert "requester-secret" not in str(exc_info.value)


def test_requester_canary_module_never_reads_provider_key_env_var() -> None:
    module_path = Path("scripts/croo_requester_canary.py")
    text = module_path.read_text(encoding="utf-8")
    # The provider's own env var name may appear in an explanatory comment/
    # docstring (contrasting it with CROO_REQUESTER_SDK_KEY); what must never
    # appear is actual code reading it.
    forbidden_reads = (
        '"CROO_SDK_KEY"]',
        'get("CROO_SDK_KEY"',
        'getenv("CROO_SDK_KEY"',
    )
    for pattern in forbidden_reads:
        assert pattern not in text
    assert "CROO_REQUESTER_SDK_KEY" in text


def test_requester_canary_has_no_wallet_or_private_key_or_retry_loop() -> None:
    module_path = Path("scripts/croo_requester_canary.py")
    text = module_path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    forbidden_terms = ("private_key", "wallet", "sign(", "broadcast", "swap")
    lowered = text.lower()
    for term in forbidden_terms:
        assert term not in lowered
    for node in ast.walk(tree):
        assert not isinstance(node, (ast.For, ast.While)), (
            "no retry loop should be implemented in the requester canary"
        )
