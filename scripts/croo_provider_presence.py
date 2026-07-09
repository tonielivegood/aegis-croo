from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from importlib import import_module
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.aegis_croo.cap.config import configured_provider_presence_enabled
from src.aegis_croo.cap.provider_presence_runtime import ProviderPresenceRuntime
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


def _create_sdk_client():
    croo_sdk = import_module("croo")
    api_url = os.environ.get("CROO_API_URL", "https://api.croo.network")
    ws_url = os.environ["CROO_WS_URL"]
    sdk_key = os.environ["CROO_SDK_KEY"]
    return croo_sdk.AgentClient(
        croo_sdk.Config(base_url=api_url, ws_url=ws_url), sdk_key
    )


async def run_presence() -> int:
    """Persistent provider presence only: connect and hold the connection open.

    Registers no event handlers and calls no CAP lifecycle method. Refuses to
    connect unless CAP_PROVIDER_PRESENCE_ENABLED is explicitly true.
    """
    if not configured_provider_presence_enabled():
        print(
            "CAP_PROVIDER_PRESENCE_ENABLED must be true to start the "
            "persistent provider-presence runtime. Refusing to connect.",
            file=sys.stderr,
        )
        return 1

    missing = [
        name
        for name in ("CROO_WS_URL", "CROO_SDK_KEY")
        if not os.environ.get(name)
    ]
    if missing:
        print(
            "Missing required environment variables: " + ", ".join(missing),
            file=sys.stderr,
        )
        return 1

    _configure_sanitized_logging()

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _handle_sigint(*_args: object) -> None:
        loop.call_soon_threadsafe(stop_event.set)

    signal.signal(signal.SIGINT, _handle_sigint)

    print(
        "Persistent provider-presence runtime starting "
        "(observe-only; no CAP lifecycle method will be called). "
        "Press Ctrl+C to stop.",
        file=sys.stderr,
    )

    runtime = ProviderPresenceRuntime(client_factory=_create_sdk_client)
    result = await runtime.run(stop_event)
    print(result.model_dump_json(), flush=True)
    return 0 if result.connected and result.closed else 1


def main() -> int:
    return asyncio.run(run_presence())


if __name__ == "__main__":
    raise SystemExit(main())
