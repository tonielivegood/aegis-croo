from __future__ import annotations

import asyncio
import re
from collections.abc import Mapping
from typing import Any, Protocol


REDACTED = "[REDACTED]"
REDACTED_WEBSOCKET_URL = "[REDACTED_WEBSOCKET_URL]"
_CROO_KEY_PATTERN = re.compile(r"croo_sk_[a-z0-9._-]+", re.IGNORECASE)
_CREDENTIAL_WS_URL_PATTERN = re.compile(
    r"\bwss?://[^\s\"']*(?:\?|@)[^\s\"']*",
    re.IGNORECASE,
)
_CREDENTIAL_PARAMETER_PATTERN = re.compile(
    r"(\b(?:key|sdk[_-]?key|api[_-]?key|token)\s*=\s*)[^\s&#,;]+",
    re.IGNORECASE,
)
_CREDENTIAL_HEADER_PATTERN = re.compile(
    r"(\b(?:x-sdk-key|authorization|proxy-authorization)\b\s*[:=]\s*)"
    r"[^\r\n,;]+",
    re.IGNORECASE,
)
_SENSITIVE_HEADER_NAMES = {
    "authorization",
    "proxy-authorization",
    "x-api-key",
    "x-sdk-key",
}


class CloseableStream(Protocol):
    async def close(self) -> None: ...


def redact_sensitive_text(value: str) -> str:
    redacted = _CREDENTIAL_WS_URL_PATTERN.sub(REDACTED_WEBSOCKET_URL, value)
    redacted = _CREDENTIAL_HEADER_PATTERN.sub(
        lambda match: f"{match.group(1)}{REDACTED}",
        redacted,
    )
    redacted = _CREDENTIAL_PARAMETER_PATTERN.sub(
        lambda match: f"{match.group(1)}{REDACTED}",
        redacted,
    )
    return _CROO_KEY_PATTERN.sub(REDACTED, redacted)


def redact_headers(headers: Mapping[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for name, value in headers.items():
        if name.casefold() in _SENSITIVE_HEADER_NAMES:
            result[name] = REDACTED
        else:
            result[name] = redact_sensitive_text(str(value))
    return result


async def bounded_close(
    stream: CloseableStream,
    *,
    timeout_seconds: float,
) -> tuple[bool, str | None]:
    try:
        await asyncio.wait_for(stream.close(), timeout=timeout_seconds)
    except Exception as exc:
        return False, redact_sensitive_text(str(exc))
    return True, None
