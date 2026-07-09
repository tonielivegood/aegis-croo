from __future__ import annotations

import json
import os
import sys
from importlib import import_module
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.aegis_croo.cap.config import load_requester_canary_config
from src.aegis_croo.cap.ws_safety import redact_sensitive_text


def _create_requester_client() -> Any:
    """Build a requester-side SDK client.

    Deliberately reads CROO_REQUESTER_SDK_KEY, never CROO_SDK_KEY (the
    provider's own key), so the two roles can never accidentally share a
    credential.
    """
    croo_sdk = import_module("croo")
    api_url = os.environ.get("CROO_API_URL", "https://api.croo.network")
    ws_url = os.environ.get("CROO_WS_URL", "")
    sdk_key = os.environ["CROO_REQUESTER_SDK_KEY"]
    return croo_sdk.AgentClient(croo_sdk.Config(base_url=api_url, ws_url=ws_url), sdk_key)


async def negotiate(requirements: dict[str, Any]) -> Any:
    """Negotiate exactly one order against the expected provider Service ID.

    Requires CAP_REQUESTER_CANARY_ENABLED=true. This is a standalone
    requester-role action, outside Aegis Core, for one future controlled
    A2A test only. No retry loop is implemented.
    """
    gates = load_requester_canary_config()
    if not gates.canary_enabled:
        raise RuntimeError("CAP_REQUESTER_CANARY_ENABLED must be true to negotiate.")
    if gates.missing_allowlist:
        raise RuntimeError(
            "Missing required allowlist configuration: "
            + ", ".join(gates.missing_allowlist)
        )
    if not os.environ.get("CROO_REQUESTER_SDK_KEY"):
        raise RuntimeError("CROO_REQUESTER_SDK_KEY is required.")

    croo_sdk = import_module("croo")
    client = _create_requester_client()
    try:
        request = croo_sdk.NegotiateOrderRequest(
            service_id=gates.expected_provider_service_id,
            requirements=json.dumps(
                requirements, sort_keys=True, separators=(",", ":")
            ),
        )
        return await client.negotiate_order(request)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(redact_sensitive_text(str(exc))) from None
    finally:
        await client.close()


async def pay(order_id: str) -> Any:
    """Pay exactly one order.

    Requires both CAP_REQUESTER_CANARY_ENABLED=true and an independent
    CAP_REQUESTER_PAY_ENABLED=true. No retry loop is implemented.
    """
    gates = load_requester_canary_config()
    if not gates.canary_enabled or not gates.pay_enabled:
        raise RuntimeError(
            "CAP_REQUESTER_CANARY_ENABLED and CAP_REQUESTER_PAY_ENABLED must "
            "both be true to pay."
        )
    if not os.environ.get("CROO_REQUESTER_SDK_KEY"):
        raise RuntimeError("CROO_REQUESTER_SDK_KEY is required.")

    client = _create_requester_client()
    try:
        return await client.pay_order(order_id)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(redact_sensitive_text(str(exc))) from None
    finally:
        await client.close()


def main() -> int:
    print(
        "This script exposes negotiate()/pay() for one future controlled "
        "requester canary test only. It does not auto-run a live order; "
        "import it and call the functions explicitly under separate owner "
        "authorization.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
