from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from importlib import import_module
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.aegis_croo.cap.config import load_lifecycle_canary_config
from src.aegis_croo.cap.provider_lifecycle_runtime import ProviderLifecycleRuntime
from src.aegis_croo.cap.ws_safety import redact_sensitive_text


class _RedactingLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_sensitive_text(record.getMessage())
        record.args = ()
        return True


def _configure_sanitized_logging() -> None:
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.WARNING)
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    handler.addFilter(_RedactingLogFilter())

    for logger_name in ("croo", "websockets"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
        logger.propagate = False


class _RealLifecycleClientAdapter:
    """Adapts the installed croo-sdk AgentClient to the LifecycleClient protocol.

    Only this adapter (never provider_lifecycle_runtime.py) constructs the
    real SDK's DeliverOrderRequest dataclass, keeping the runtime module
    itself free of any croo import.
    """

    def __init__(self, agent_client: Any, croo_sdk: Any) -> None:
        self._client = agent_client
        self._croo_sdk = croo_sdk

    async def connect_websocket(self) -> Any:
        return await self._client.connect_websocket()

    async def get_negotiation(self, negotiation_id: str) -> Any:
        return await self._client.get_negotiation(negotiation_id)

    async def accept_negotiation(self, negotiation_id: str) -> Any:
        return await self._client.accept_negotiation(negotiation_id)

    async def get_order(self, order_id: str) -> Any:
        return await self._client.get_order(order_id)

    async def deliver_order(
        self,
        order_id: str,
        *,
        deliverable_type: str,
        deliverable_schema: str,
        deliverable_text: str,
    ) -> Any:
        request = self._croo_sdk.DeliverOrderRequest(
            deliverable_type=deliverable_type,
            deliverable_schema=deliverable_schema,
            deliverable_text=deliverable_text,
        )
        return await self._client.deliver_order(order_id, request)

    async def close(self) -> None:
        await self._client.close()


def _create_lifecycle_client() -> _RealLifecycleClientAdapter:
    croo_sdk = import_module("croo")
    api_url = os.environ.get("CROO_API_URL", "https://api.croo.network")
    ws_url = os.environ["CROO_WS_URL"]
    sdk_key = os.environ["CROO_SDK_KEY"]
    agent_client = croo_sdk.AgentClient(
        croo_sdk.Config(base_url=api_url, ws_url=ws_url), sdk_key
    )
    return _RealLifecycleClientAdapter(agent_client, croo_sdk)


async def run_lifecycle() -> int:
    """Gated, single-order real CAP lifecycle wiring.

    Refuses to connect unless CAP_REAL_LIFECYCLE_ENABLED is true and the
    service/requester allowlist is fully configured. Never calls
    reject_negotiation, reject_order, accept_negotiation_with_fund_address,
    or upload_file.
    """
    gates = load_lifecycle_canary_config()
    if not gates.lifecycle_enabled:
        print(
            "CAP_REAL_LIFECYCLE_ENABLED must be true to start the lifecycle "
            "runtime. Refusing to connect.",
            file=sys.stderr,
        )
        return 1
    if gates.missing_allowlist:
        print(
            "Missing required allowlist configuration: "
            + ", ".join(gates.missing_allowlist),
            file=sys.stderr,
        )
        return 1

    missing_env = [
        name for name in ("CROO_WS_URL", "CROO_SDK_KEY") if not os.environ.get(name)
    ]
    if missing_env:
        print(
            "Missing required environment variables: " + ", ".join(missing_env),
            file=sys.stderr,
        )
        return 1

    _configure_sanitized_logging()

    client = _create_lifecycle_client()
    runtime = ProviderLifecycleRuntime(client=client, gates=gates)

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _handle_sigint(*_args: object) -> None:
        loop.call_soon_threadsafe(stop_event.set)

    signal.signal(signal.SIGINT, _handle_sigint)

    print(
        "Gated provider lifecycle runtime starting "
        f"(accept_enabled={gates.accept_enabled}, deliver_enabled={gates.deliver_enabled}). "
        "Maximum one negotiation accepted, one order delivered this run. "
        "Press Ctrl+C to stop.",
        file=sys.stderr,
    )

    stream = await client.connect_websocket()
    runtime.register_handlers(stream)
    try:
        await stop_event.wait()
    finally:
        await stream.close()
        await client.close()
    return 0


def main() -> int:
    return asyncio.run(run_lifecycle())


if __name__ == "__main__":
    raise SystemExit(main())
