import ast
from pathlib import Path

import pytest

from src.aegis_croo.cap.config import configured_provider_presence_enabled
from src.aegis_croo.cap.provider_presence_runtime import (
    ProviderPresenceDisabledError,
    ProviderPresenceRuntime,
)


class FakeStream:
    def __init__(self) -> None:
        self.close_calls = 0

    async def close(self) -> None:
        self.close_calls += 1


class FakeClient:
    def __init__(self, stream: FakeStream, *, connect_error: Exception | None = None) -> None:
        self._stream = stream
        self._connect_error = connect_error
        self.connect_calls = 0
        self.close_calls = 0

    async def connect_websocket(self) -> FakeStream:
        self.connect_calls += 1
        if self._connect_error is not None:
            raise self._connect_error
        return self._stream

    async def close(self) -> None:
        self.close_calls += 1


def test_explicit_opt_in_is_required(monkeypatch) -> None:
    monkeypatch.delenv("CAP_PROVIDER_PRESENCE_ENABLED", raising=False)
    assert configured_provider_presence_enabled() is False

    factory_calls = 0

    def factory():
        nonlocal factory_calls
        factory_calls += 1
        raise AssertionError("client_factory must not be called without opt-in")

    with pytest.raises(ProviderPresenceDisabledError):
        ProviderPresenceRuntime.from_environment(client_factory=factory)
    assert factory_calls == 0


def test_opt_in_enabled_permits_construction(monkeypatch) -> None:
    monkeypatch.setenv("CAP_PROVIDER_PRESENCE_ENABLED", "true")
    runtime = ProviderPresenceRuntime.from_environment(client_factory=lambda: None)
    assert isinstance(runtime, ProviderPresenceRuntime)


@pytest.mark.anyio
async def test_connect_websocket_called_exactly_once_and_stays_alive_until_stopped() -> None:
    import asyncio

    stream = FakeStream()
    client = FakeClient(stream)
    runtime = ProviderPresenceRuntime(client_factory=lambda: client)

    stop_event = asyncio.Event()
    task = asyncio.create_task(runtime.run(stop_event))

    await asyncio.sleep(0.05)
    assert not task.done()
    assert client.connect_calls == 1

    stop_event.set()
    result = await asyncio.wait_for(task, timeout=1.0)

    assert result.connected is True
    assert result.closed is True
    assert stream.close_calls == 1
    assert client.close_calls == 1
    assert client.connect_calls == 1


@pytest.mark.anyio
async def test_clean_close_on_cancellation() -> None:
    import asyncio

    stream = FakeStream()
    client = FakeClient(stream)
    runtime = ProviderPresenceRuntime(client_factory=lambda: client)

    stop_event = asyncio.Event()
    task = asyncio.create_task(runtime.run(stop_event))
    await asyncio.sleep(0.05)
    assert not task.done()

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert stream.close_calls == 1
    assert client.close_calls == 1


@pytest.mark.anyio
async def test_connection_failure_is_reported_without_leaking_secret() -> None:
    error = RuntimeError("failed wss://api.croo.network/ws?key=croo_sk_test-secret")
    client = FakeClient(FakeStream(), connect_error=error)
    runtime = ProviderPresenceRuntime(client_factory=lambda: client)

    import asyncio

    result = await runtime.run(asyncio.Event())

    assert result.connected is False
    assert result.error is not None
    assert "croo_sk_" not in result.error
    assert "test-secret" not in result.error


def test_import_alone_causes_no_connection() -> None:
    factory_calls = 0

    def factory():
        nonlocal factory_calls
        factory_calls += 1
        raise AssertionError("import must never trigger a connection")

    # Constructing the runtime object itself must not call the factory either.
    ProviderPresenceRuntime(client_factory=factory)
    assert factory_calls == 0


def test_runtime_module_has_no_mutating_or_network_calls() -> None:
    module_path = Path("src/aegis_croo/cap/provider_presence_runtime.py")
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
    forbidden_imports = {"croo", "websocket", "websockets", "requests", "httpx", "aiohttp"}

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
