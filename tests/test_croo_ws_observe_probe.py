import ast
import logging
from pathlib import Path

import pytest

from scripts.croo_ws_observe_probe import (
    ProbePreflightError,
    RedactingLogFilter,
    run_probe,
)


class FakeStream:
    def __init__(self, event: dict | None = None) -> None:
        self._handler = None
        self._event = event
        self.close_calls = 0
        self.unsafe_calls: list[str] = []

    def on_any(self, handler) -> None:
        self._handler = handler

    async def connect(self) -> None:
        if self._event is not None:
            assert self._handler is not None
            self._handler(self._event)

    async def close(self) -> None:
        self.close_calls += 1

    def __getattr__(self, name: str):
        forbidden = {
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
        if name not in forbidden:
            raise AttributeError(name)

        def record_unsafe_call(*args, **kwargs) -> None:
            self.unsafe_calls.append(name)

        return record_unsafe_call


def set_probe_env(monkeypatch) -> None:
    monkeypatch.setenv("CAP_MODE", "mock")
    monkeypatch.setenv("CAP_REAL_PROVIDER_ENABLED", "false")
    monkeypatch.setenv("CAP_WS_OBSERVE_ONLY_ENABLED", "true")
    monkeypatch.setenv("CAP_WS_OBSERVE_TIMEOUT_SECONDS", "0.01")
    monkeypatch.setenv("CROO_WS_URL", "wss://api.croo.network/ws")
    monkeypatch.setenv("CROO_SDK_KEY", "croo_sk_test-secret")
    monkeypatch.setenv("CROO_SERVICE_ID", "service-test-secret")


@pytest.mark.anyio
async def test_probe_reports_verified_only_after_connected_timeout(
    monkeypatch,
) -> None:
    set_probe_env(monkeypatch)
    stream = FakeStream()

    report = await run_probe(stream_factory=lambda *_args: stream)

    serialized = report.model_dump_json()
    assert report.probe_status == "verified_observe_only"
    assert report.websocket_connection_status == "verified_observe_only"
    assert report.agent_online_status == "observed_connection_only"
    assert report.real_cap_ready is False
    assert report.closed is True
    assert stream.close_calls == 1
    assert stream.unsafe_calls == []
    assert "croo_sk_" not in serialized
    assert "service-test-secret" not in serialized


@pytest.mark.anyio
async def test_probe_aborts_on_event_without_mutation(monkeypatch) -> None:
    set_probe_env(monkeypatch)
    stream = FakeStream(
        {
            "type": "order_negotiation_created",
            "negotiation_id": "sensitive-negotiation-id",
        }
    )

    report = await run_probe(stream_factory=lambda *_args: stream)

    serialized = report.model_dump_json()
    assert report.probe_status == "observe_abort"
    assert report.websocket_connection_status == "observe_abort"
    assert report.real_cap_ready is False
    assert report.closed is True
    assert "sensitive-negotiation-id" not in serialized
    assert stream.unsafe_calls == []


@pytest.mark.anyio
async def test_probe_refuses_when_observe_gate_is_disabled(monkeypatch) -> None:
    set_probe_env(monkeypatch)
    monkeypatch.setenv("CAP_WS_OBSERVE_ONLY_ENABLED", "false")
    factory_calls = 0

    def stream_factory(*_args):
        nonlocal factory_calls
        factory_calls += 1
        return FakeStream()

    with pytest.raises(ProbePreflightError):
        await run_probe(stream_factory=stream_factory)
    assert factory_calls == 0


def test_probe_log_filter_redacts_key_service_id_and_url() -> None:
    record = logging.LogRecord(
        name="croo",
        level=logging.WARNING,
        pathname=__file__,
        lineno=1,
        msg=(
            "failed wss://api.croo.network/ws?key=croo_sk_log-secret "
            "service-test-secret X-SDK-Key: croo_sk_header-secret"
        ),
        args=(),
        exc_info=None,
    )

    assert RedactingLogFilter(
        ["croo_sk_log-secret", "service-test-secret"]
    ).filter(record)
    message = record.getMessage()
    assert "croo_sk_" not in message
    assert "service-test-secret" not in message
    assert "wss://api.croo.network/ws?key=" not in message


def test_probe_module_has_lazy_sdk_import_and_no_mutating_calls() -> None:
    module_path = Path("scripts/croo_ws_observe_probe.py")
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

    assert "croo" not in imported_roots
    assert forbidden_calls.isdisjoint(called_names)
