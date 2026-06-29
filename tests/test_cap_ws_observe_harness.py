import ast
from pathlib import Path

import pytest

from src.aegis_croo.cap.config import (
    configured_ws_observe_enabled,
    configured_ws_observe_timeout_seconds,
)
from src.aegis_croo.cap.ws_observe_harness import (
    ObserveOnlyDisabledError,
    ObserveOnlyWebSocketHarness,
    redact_headers,
    redact_sensitive_text,
)


class FakeStream:
    def __init__(self) -> None:
        self.handler = None
        self.close_calls = 0
        self.unsafe_calls: list[str] = []

    def on_any(self, handler) -> None:
        self.handler = handler

    async def close(self) -> None:
        self.close_calls += 1

    def emit(self, event) -> None:
        assert self.handler is not None
        self.handler(event)

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


@pytest.mark.anyio
async def test_observe_harness_is_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("CAP_WS_OBSERVE_ONLY_ENABLED", raising=False)
    monkeypatch.delenv("CAP_WS_OBSERVE_TIMEOUT_SECONDS", raising=False)
    stream = FakeStream()
    connect_calls = 0

    async def connect(_stream) -> None:
        nonlocal connect_calls
        connect_calls += 1

    harness = ObserveOnlyWebSocketHarness.from_environment()

    assert configured_ws_observe_enabled() is False
    assert configured_ws_observe_timeout_seconds() > 0
    with pytest.raises(ObserveOnlyDisabledError):
        await harness.run(stream, connect)
    assert connect_calls == 0
    assert stream.close_calls == 0


def test_redaction_removes_sdk_keys_headers_and_credential_urls() -> None:
    text = (
        "connecting wss://api.croo.network/ws?key=croo_sk_query-secret "
        "X-SDK-Key: croo_sk_header-secret "
        "sdk_key=croo_sk_parameter-secret raw=croo_sk_raw-secret"
    )

    redacted = redact_sensitive_text(text)
    headers = redact_headers(
        {
            "X-SDK-Key": "croo_sk_header-secret",
            "Authorization": "Bearer croo_sk_bearer-secret",
            "X-Trace": "safe",
        }
    )

    assert "croo_sk_" not in redacted
    assert "query-secret" not in redacted
    assert "header-secret" not in redacted
    assert "parameter-secret" not in redacted
    assert "raw-secret" not in redacted
    assert "wss://api.croo.network/ws?key=" not in redacted
    assert headers["X-SDK-Key"] == "[REDACTED]"
    assert "croo_sk_" not in headers["Authorization"]
    assert headers["X-Trace"] == "safe"


@pytest.mark.anyio
async def test_timeout_closes_fake_stream(monkeypatch) -> None:
    monkeypatch.setenv("CAP_WS_OBSERVE_ONLY_ENABLED", "true")
    monkeypatch.setenv("CAP_WS_OBSERVE_TIMEOUT_SECONDS", "0.01")
    stream = FakeStream()

    async def connect(_stream) -> None:
        return None

    result = await ObserveOnlyWebSocketHarness.from_environment().run(
        stream,
        connect,
    )

    assert result.status == "timed_out"
    assert result.closed is True
    assert result.close_attempted is True
    assert result.local_only is True
    assert result.real_cap_ready is False
    assert stream.close_calls == 1


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("event_type", "id_field"),
    [
        ("order_negotiation_created", "negotiation_id"),
        ("order_paid", "order_id"),
    ],
)
async def test_incoming_event_aborts_and_closes(
    monkeypatch,
    event_type: str,
    id_field: str,
) -> None:
    monkeypatch.setenv("CAP_WS_OBSERVE_ONLY_ENABLED", "true")
    stream = FakeStream()
    sensitive_id = "must-not-be-serialized"

    async def connect(connected_stream: FakeStream) -> None:
        connected_stream.emit(
            {
                "type": event_type,
                id_field: sensitive_id,
                "raw": {"sdk_key": "croo_sk_never-return"},
            }
        )

    result = await ObserveOnlyWebSocketHarness.from_environment().run(
        stream,
        connect,
    )

    serialized = result.model_dump_json()
    assert result.status == "event_aborted"
    assert result.event is not None
    assert result.event.event_type == event_type
    assert result.closed is True
    assert sensitive_id not in serialized
    assert "croo_sk_" not in serialized
    assert stream.close_calls == 1
    assert stream.unsafe_calls == []


@pytest.mark.anyio
async def test_connector_exception_is_sanitized_and_stream_still_closes(
    monkeypatch,
) -> None:
    monkeypatch.setenv("CAP_WS_OBSERVE_ONLY_ENABLED", "true")
    stream = FakeStream()

    async def connect(_stream) -> None:
        raise RuntimeError(
            "failed wss://api.croo.network/ws?key=croo_sk_exception-secret"
        )

    result = await ObserveOnlyWebSocketHarness.from_environment().run(
        stream,
        connect,
    )

    assert result.status == "error"
    assert result.closed is True
    assert result.error is not None
    assert "croo_sk_" not in result.error
    assert "exception-secret" not in result.error
    assert stream.close_calls == 1


def test_harness_module_has_no_sdk_network_or_mutating_calls() -> None:
    module_path = Path("src/aegis_croo/cap/ws_observe_harness.py")
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    forbidden_imports = {
        "croo",
        "websocket",
        "websockets",
        "requests",
        "httpx",
        "aiohttp",
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
