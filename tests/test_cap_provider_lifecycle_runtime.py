import ast
import json
from pathlib import Path

import pytest

from src.aegis_croo.cap.config import (
    LifecycleCanaryConfig,
    configured_accept_negotiation_enabled,
    configured_deliver_order_enabled,
    configured_real_lifecycle_enabled,
)
from src.aegis_croo.cap.provider_lifecycle_runtime import ProviderLifecycleRuntime


SAFE_BUY = {
    "token": "BNB",
    "chain": "bsc",
    "intended_action": "buy",
    "size_usd": 100,
    "market_signal": {
        "price_change_24h": 1.0,
        "volume_change_24h": 8.0,
        "liquidity_usd": 500_000,
        "volatility_24h": 2.0,
    },
}
BLOCK_BUY = dict(SAFE_BUY, market_signal={
    "price_change_24h": -8.0,
    "volume_change_24h": -10.0,
    "liquidity_usd": 50_000,
    "volatility_24h": 9.0,
})
WAIT_BUY = dict(SAFE_BUY)
WAIT_BUY["market_signal"] = dict(WAIT_BUY["market_signal"])
del WAIT_BUY["market_signal"]["liquidity_usd"]

EXPECTED_SERVICE_ID = "svc-real-123"
EXPECTED_REQUESTER_AGENT_ID = "req-agent-real-456"


def make_gates(**overrides) -> LifecycleCanaryConfig:
    defaults = dict(
        lifecycle_enabled=True,
        accept_enabled=True,
        deliver_enabled=True,
        expected_service_id=EXPECTED_SERVICE_ID,
        expected_requester_agent_id=EXPECTED_REQUESTER_AGENT_ID,
    )
    defaults.update(overrides)
    return LifecycleCanaryConfig(**defaults)


class FakeEvent:
    def __init__(self, *, negotiation_id: str = "", order_id: str = "") -> None:
        self.negotiation_id = negotiation_id
        self.order_id = order_id


class FakeNegotiation:
    def __init__(
        self,
        *,
        service_id: str,
        requester_agent_id: str,
        requirements: str,
        fund_amount: str = "",
        fund_token: str = "",
    ) -> None:
        self.service_id = service_id
        self.requester_agent_id = requester_agent_id
        self.requirements = requirements
        self.fund_amount = fund_amount
        self.fund_token = fund_token


class FakeOrder:
    def __init__(
        self,
        *,
        service_id: str,
        requester_agent_id: str,
        negotiation_id: str,
        status: str = "paid",
    ) -> None:
        self.service_id = service_id
        self.requester_agent_id = requester_agent_id
        self.negotiation_id = negotiation_id
        self.status = status


class FakeStream:
    def __init__(self) -> None:
        self.handlers: dict[str, object] = {}

    def on(self, event_type: str, handler) -> None:
        self.handlers[event_type] = handler

    async def close(self) -> None:
        pass


class FakeClient:
    def __init__(
        self,
        *,
        negotiation: FakeNegotiation | None = None,
        order: FakeOrder | None = None,
        get_negotiation_error: Exception | None = None,
        get_order_error: Exception | None = None,
        accept_error: Exception | None = None,
        deliver_error: Exception | None = None,
    ) -> None:
        self.negotiation = negotiation
        self.order = order
        self.get_negotiation_calls: list[str] = []
        self.get_order_calls: list[str] = []
        self.accept_calls: list[str] = []
        self.deliver_calls: list[tuple[str, str, str, str]] = []
        self._get_negotiation_error = get_negotiation_error
        self._get_order_error = get_order_error
        self._accept_error = accept_error
        self._deliver_error = deliver_error

    async def get_negotiation(self, negotiation_id: str):
        self.get_negotiation_calls.append(negotiation_id)
        if self._get_negotiation_error:
            raise self._get_negotiation_error
        return self.negotiation

    async def accept_negotiation(self, negotiation_id: str):
        self.accept_calls.append(negotiation_id)
        if self._accept_error:
            raise self._accept_error
        return None

    async def get_order(self, order_id: str):
        self.get_order_calls.append(order_id)
        if self._get_order_error:
            raise self._get_order_error
        return self.order

    async def deliver_order(
        self, order_id: str, *, deliverable_type: str, deliverable_schema: str, deliverable_text: str
    ):
        self.deliver_calls.append(
            (order_id, deliverable_type, deliverable_schema, deliverable_text)
        )
        if self._deliver_error:
            raise self._deliver_error
        return None

    async def connect_websocket(self):
        raise AssertionError("connect_websocket is not exercised by these tests")

    async def close(self) -> None:
        pass


def test_lifecycle_default_disabled(monkeypatch) -> None:
    monkeypatch.delenv("CAP_REAL_LIFECYCLE_ENABLED", raising=False)
    assert configured_real_lifecycle_enabled() is False


def test_accept_default_disabled(monkeypatch) -> None:
    monkeypatch.delenv("CAP_ACCEPT_NEGOTIATION_ENABLED", raising=False)
    assert configured_accept_negotiation_enabled() is False


def test_deliver_default_disabled(monkeypatch) -> None:
    monkeypatch.delenv("CAP_DELIVER_ORDER_ENABLED", raising=False)
    assert configured_deliver_order_enabled() is False


def test_register_handlers_wires_expected_event_types() -> None:
    runtime = ProviderLifecycleRuntime(client=FakeClient(), gates=make_gates())
    stream = FakeStream()
    runtime.register_handlers(stream)
    assert set(stream.handlers.keys()) == {"order_negotiation_created", "order_paid"}


@pytest.mark.anyio
async def test_valid_negotiation_accepts_exactly_once() -> None:
    negotiation = FakeNegotiation(
        service_id=EXPECTED_SERVICE_ID,
        requester_agent_id=EXPECTED_REQUESTER_AGENT_ID,
        requirements=json.dumps(SAFE_BUY),
    )
    client = FakeClient(negotiation=negotiation)
    runtime = ProviderLifecycleRuntime(client=client, gates=make_gates())

    outcome = await runtime.handle_negotiation_created(FakeEvent(negotiation_id="neg-1"))

    assert outcome.status == "accepted"
    assert client.accept_calls == ["neg-1"]


@pytest.mark.anyio
async def test_duplicate_negotiation_event_does_not_reaccept() -> None:
    negotiation = FakeNegotiation(
        service_id=EXPECTED_SERVICE_ID,
        requester_agent_id=EXPECTED_REQUESTER_AGENT_ID,
        requirements=json.dumps(SAFE_BUY),
    )
    client = FakeClient(negotiation=negotiation)
    runtime = ProviderLifecycleRuntime(client=client, gates=make_gates())
    event = FakeEvent(negotiation_id="neg-1")

    first = await runtime.handle_negotiation_created(event)
    second = await runtime.handle_negotiation_created(event)

    assert first.status == "accepted"
    assert second.status == "rejected_locally"
    assert second.reason_code == "duplicate_negotiation_event"
    assert client.accept_calls == ["neg-1"]


@pytest.mark.anyio
async def test_wrong_service_id_does_not_accept() -> None:
    negotiation = FakeNegotiation(
        service_id="wrong-service",
        requester_agent_id=EXPECTED_REQUESTER_AGENT_ID,
        requirements=json.dumps(SAFE_BUY),
    )
    client = FakeClient(negotiation=negotiation)
    runtime = ProviderLifecycleRuntime(client=client, gates=make_gates())

    outcome = await runtime.handle_negotiation_created(FakeEvent(negotiation_id="neg-2"))

    assert outcome.status == "rejected_locally"
    assert outcome.reason_code == "service_id_mismatch"
    assert client.accept_calls == []


@pytest.mark.anyio
async def test_wrong_requester_identity_does_not_accept() -> None:
    negotiation = FakeNegotiation(
        service_id=EXPECTED_SERVICE_ID,
        requester_agent_id="someone-else",
        requirements=json.dumps(SAFE_BUY),
    )
    client = FakeClient(negotiation=negotiation)
    runtime = ProviderLifecycleRuntime(client=client, gates=make_gates())

    outcome = await runtime.handle_negotiation_created(FakeEvent(negotiation_id="neg-3"))

    assert outcome.status == "rejected_locally"
    assert outcome.reason_code == "requester_agent_id_mismatch"
    assert client.accept_calls == []


@pytest.mark.anyio
async def test_malformed_requirements_json_does_not_accept() -> None:
    negotiation = FakeNegotiation(
        service_id=EXPECTED_SERVICE_ID,
        requester_agent_id=EXPECTED_REQUESTER_AGENT_ID,
        requirements="not-json{{",
    )
    client = FakeClient(negotiation=negotiation)
    runtime = ProviderLifecycleRuntime(client=client, gates=make_gates())

    outcome = await runtime.handle_negotiation_created(FakeEvent(negotiation_id="neg-4"))

    assert outcome.status == "rejected_locally"
    assert outcome.reason_code == "requirements_not_valid_json"
    assert client.accept_calls == []


@pytest.mark.anyio
async def test_requirements_failing_guard_schema_does_not_accept() -> None:
    negotiation = FakeNegotiation(
        service_id=EXPECTED_SERVICE_ID,
        requester_agent_id=EXPECTED_REQUESTER_AGENT_ID,
        requirements=json.dumps({"token": "BNB"}),  # missing required fields
    )
    client = FakeClient(negotiation=negotiation)
    runtime = ProviderLifecycleRuntime(client=client, gates=make_gates())

    outcome = await runtime.handle_negotiation_created(FakeEvent(negotiation_id="neg-5"))

    assert outcome.status == "rejected_locally"
    assert outcome.reason_code == "guard_rejected"
    assert client.accept_calls == []


@pytest.mark.anyio
async def test_fund_transfer_negotiation_is_rejected_not_accepted() -> None:
    negotiation = FakeNegotiation(
        service_id=EXPECTED_SERVICE_ID,
        requester_agent_id=EXPECTED_REQUESTER_AGENT_ID,
        requirements=json.dumps(SAFE_BUY),
        fund_amount="1000",
        fund_token="0x0000000000000000000000000000000000dead",
    )
    client = FakeClient(negotiation=negotiation)
    runtime = ProviderLifecycleRuntime(client=client, gates=make_gates())

    outcome = await runtime.handle_negotiation_created(FakeEvent(negotiation_id="neg-6"))

    assert outcome.status == "rejected_locally"
    assert outcome.reason_code == "guard_rejected"
    assert client.accept_calls == []


async def _accept_then_pay(requirements: dict, *, gates: LifecycleCanaryConfig | None = None):
    negotiation = FakeNegotiation(
        service_id=EXPECTED_SERVICE_ID,
        requester_agent_id=EXPECTED_REQUESTER_AGENT_ID,
        requirements=json.dumps(requirements),
    )
    order = FakeOrder(
        service_id=EXPECTED_SERVICE_ID,
        requester_agent_id=EXPECTED_REQUESTER_AGENT_ID,
        negotiation_id="neg-1",
        status="paid",
    )
    client = FakeClient(negotiation=negotiation, order=order)
    runtime = ProviderLifecycleRuntime(client=client, gates=gates or make_gates())
    await runtime.handle_negotiation_created(FakeEvent(negotiation_id="neg-1"))
    outcome = await runtime.handle_order_paid(FakeEvent(order_id="order-1"))
    return outcome, client


@pytest.mark.anyio
async def test_paid_order_runs_risk_engine_and_delivers_execute() -> None:
    outcome, client = await _accept_then_pay(SAFE_BUY)
    assert outcome.status == "delivered"
    assert outcome.decision == "EXECUTE"
    assert len(client.deliver_calls) == 1
    order_id, deliverable_type, deliverable_schema, _ = client.deliver_calls[0]
    assert order_id == "order-1"
    assert deliverable_type == "schema"
    assert json.loads(deliverable_schema)["decision"] == "EXECUTE"


@pytest.mark.anyio
async def test_paid_order_runs_risk_engine_and_delivers_block() -> None:
    outcome, client = await _accept_then_pay(BLOCK_BUY)
    assert outcome.status == "delivered"
    assert outcome.decision == "BLOCK"
    assert json.loads(client.deliver_calls[0][2])["decision"] == "BLOCK"


@pytest.mark.anyio
async def test_paid_order_runs_risk_engine_and_delivers_wait() -> None:
    outcome, client = await _accept_then_pay(WAIT_BUY)
    assert outcome.status == "delivered"
    assert outcome.decision == "WAIT"
    assert json.loads(client.deliver_calls[0][2])["decision"] == "WAIT"


@pytest.mark.anyio
async def test_duplicate_order_paid_event_does_not_redeliver() -> None:
    negotiation = FakeNegotiation(
        service_id=EXPECTED_SERVICE_ID,
        requester_agent_id=EXPECTED_REQUESTER_AGENT_ID,
        requirements=json.dumps(SAFE_BUY),
    )
    order = FakeOrder(
        service_id=EXPECTED_SERVICE_ID,
        requester_agent_id=EXPECTED_REQUESTER_AGENT_ID,
        negotiation_id="neg-1",
        status="paid",
    )
    client = FakeClient(negotiation=negotiation, order=order)
    runtime = ProviderLifecycleRuntime(client=client, gates=make_gates())
    await runtime.handle_negotiation_created(FakeEvent(negotiation_id="neg-1"))
    event = FakeEvent(order_id="order-1")

    first = await runtime.handle_order_paid(event)
    second = await runtime.handle_order_paid(event)

    assert first.status == "delivered"
    assert second.status == "stopped_locally"
    assert second.reason_code == "duplicate_order_event"
    assert len(client.deliver_calls) == 1


@pytest.mark.anyio
async def test_paid_order_without_prior_accept_is_stopped_not_defaulted() -> None:
    order = FakeOrder(
        service_id=EXPECTED_SERVICE_ID,
        requester_agent_id=EXPECTED_REQUESTER_AGENT_ID,
        negotiation_id="neg-none",
        status="paid",
    )
    client = FakeClient(order=order)
    runtime = ProviderLifecycleRuntime(client=client, gates=make_gates())

    outcome = await runtime.handle_order_paid(FakeEvent(order_id="order-x"))

    assert outcome.status == "stopped_locally"
    assert outcome.reason_code == "no_accepted_negotiation_on_record"
    assert client.deliver_calls == []


@pytest.mark.anyio
async def test_order_with_wrong_service_id_does_not_deliver() -> None:
    negotiation = FakeNegotiation(
        service_id=EXPECTED_SERVICE_ID,
        requester_agent_id=EXPECTED_REQUESTER_AGENT_ID,
        requirements=json.dumps(SAFE_BUY),
    )
    order = FakeOrder(
        service_id="wrong-service",
        requester_agent_id=EXPECTED_REQUESTER_AGENT_ID,
        negotiation_id="neg-1",
    )
    client = FakeClient(negotiation=negotiation, order=order)
    runtime = ProviderLifecycleRuntime(client=client, gates=make_gates())
    await runtime.handle_negotiation_created(FakeEvent(negotiation_id="neg-1"))

    outcome = await runtime.handle_order_paid(FakeEvent(order_id="order-1"))

    assert outcome.status == "stopped_locally"
    assert outcome.reason_code == "service_id_mismatch"
    assert client.deliver_calls == []


@pytest.mark.anyio
async def test_order_with_wrong_requester_does_not_deliver() -> None:
    negotiation = FakeNegotiation(
        service_id=EXPECTED_SERVICE_ID,
        requester_agent_id=EXPECTED_REQUESTER_AGENT_ID,
        requirements=json.dumps(SAFE_BUY),
    )
    order = FakeOrder(
        service_id=EXPECTED_SERVICE_ID,
        requester_agent_id="someone-else",
        negotiation_id="neg-1",
    )
    client = FakeClient(negotiation=negotiation, order=order)
    runtime = ProviderLifecycleRuntime(client=client, gates=make_gates())
    await runtime.handle_negotiation_created(FakeEvent(negotiation_id="neg-1"))

    outcome = await runtime.handle_order_paid(FakeEvent(order_id="order-1"))

    assert outcome.status == "stopped_locally"
    assert outcome.reason_code == "requester_agent_id_mismatch"
    assert client.deliver_calls == []


@pytest.mark.anyio
async def test_order_not_from_accepted_negotiation_does_not_deliver() -> None:
    negotiation = FakeNegotiation(
        service_id=EXPECTED_SERVICE_ID,
        requester_agent_id=EXPECTED_REQUESTER_AGENT_ID,
        requirements=json.dumps(SAFE_BUY),
    )
    order = FakeOrder(
        service_id=EXPECTED_SERVICE_ID,
        requester_agent_id=EXPECTED_REQUESTER_AGENT_ID,
        negotiation_id="neg-other",
    )
    client = FakeClient(negotiation=negotiation, order=order)
    runtime = ProviderLifecycleRuntime(client=client, gates=make_gates())
    await runtime.handle_negotiation_created(FakeEvent(negotiation_id="neg-1"))

    outcome = await runtime.handle_order_paid(FakeEvent(order_id="order-1"))

    assert outcome.status == "stopped_locally"
    assert outcome.reason_code == "order_not_from_accepted_negotiation"
    assert client.deliver_calls == []


@pytest.mark.anyio
async def test_single_negotiation_budget_blocks_second_negotiation() -> None:
    negotiation = FakeNegotiation(
        service_id=EXPECTED_SERVICE_ID,
        requester_agent_id=EXPECTED_REQUESTER_AGENT_ID,
        requirements=json.dumps(SAFE_BUY),
    )
    client = FakeClient(negotiation=negotiation)
    runtime = ProviderLifecycleRuntime(client=client, gates=make_gates())
    await runtime.handle_negotiation_created(FakeEvent(negotiation_id="neg-1"))

    second = await runtime.handle_negotiation_created(FakeEvent(negotiation_id="neg-2"))

    assert second.status == "rejected_locally"
    assert second.reason_code == "single_negotiation_budget_consumed"
    assert client.accept_calls == ["neg-1"]


@pytest.mark.anyio
async def test_disabled_gates_prevent_accept_and_deliver() -> None:
    negotiation = FakeNegotiation(
        service_id=EXPECTED_SERVICE_ID,
        requester_agent_id=EXPECTED_REQUESTER_AGENT_ID,
        requirements=json.dumps(SAFE_BUY),
    )
    client = FakeClient(negotiation=negotiation)
    runtime = ProviderLifecycleRuntime(
        client=client, gates=make_gates(lifecycle_enabled=False)
    )
    outcome = await runtime.handle_negotiation_created(FakeEvent(negotiation_id="neg-1"))
    assert outcome.status == "rejected_locally"
    assert outcome.reason_code == "lifecycle_or_accept_gate_disabled"
    assert client.accept_calls == []
    assert client.get_negotiation_calls == []


@pytest.mark.anyio
async def test_get_negotiation_failure_is_redacted() -> None:
    error = RuntimeError("failed wss://api.croo.network/ws?key=croo_sk_test-secret")
    client = FakeClient(get_negotiation_error=error)
    runtime = ProviderLifecycleRuntime(client=client, gates=make_gates())

    outcome = await runtime.handle_negotiation_created(FakeEvent(negotiation_id="neg-err"))

    assert outcome.status == "rejected_locally"
    assert outcome.error is not None
    assert "croo_sk_" not in outcome.error
    assert "test-secret" not in outcome.error


@pytest.mark.anyio
async def test_deliver_order_failure_is_redacted() -> None:
    negotiation = FakeNegotiation(
        service_id=EXPECTED_SERVICE_ID,
        requester_agent_id=EXPECTED_REQUESTER_AGENT_ID,
        requirements=json.dumps(SAFE_BUY),
    )
    order = FakeOrder(
        service_id=EXPECTED_SERVICE_ID,
        requester_agent_id=EXPECTED_REQUESTER_AGENT_ID,
        negotiation_id="neg-1",
    )
    error = RuntimeError("failed key=croo_sk_deliver-secret")
    client = FakeClient(negotiation=negotiation, order=order, deliver_error=error)
    runtime = ProviderLifecycleRuntime(client=client, gates=make_gates())
    await runtime.handle_negotiation_created(FakeEvent(negotiation_id="neg-1"))

    outcome = await runtime.handle_order_paid(FakeEvent(order_id="order-1"))

    assert outcome.status == "stopped_locally"
    assert outcome.error is not None
    assert "croo_sk_" not in outcome.error
    assert "deliver-secret" not in outcome.error


def test_runtime_module_has_no_croo_import_and_no_forbidden_calls() -> None:
    module_path = Path("src/aegis_croo/cap/provider_lifecycle_runtime.py")
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
    # accept_negotiation and deliver_order ARE expected (gated, narrow scope).
    assert "accept_negotiation" in called_names
    assert "deliver_order" in called_names


def test_delivery_mapping_module_has_no_croo_import() -> None:
    module_path = Path("src/aegis_croo/cap/delivery_mapping.py")
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
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
    assert {"croo", "websockets", "httpx"}.isdisjoint(imported_roots)


def test_apps_does_not_reference_lifecycle_runtime() -> None:
    apps_dir = Path("apps")
    for path in apps_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "provider_lifecycle_runtime" not in text
        assert "ProviderLifecycleRuntime" not in text
