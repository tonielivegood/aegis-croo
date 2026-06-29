import pytest

from src.aegis_croo.cap.ws_safety import bounded_close, redact_sensitive_text


class ClosingStream:
    def __init__(self, error: Exception | None = None) -> None:
        self.close_calls = 0
        self.error = error

    async def close(self) -> None:
        self.close_calls += 1
        if self.error is not None:
            raise self.error


@pytest.mark.anyio
async def test_bounded_close_closes_once() -> None:
    stream = ClosingStream()

    closed, error = await bounded_close(stream, timeout_seconds=0.1)

    assert closed is True
    assert error is None
    assert stream.close_calls == 1


@pytest.mark.anyio
async def test_bounded_close_redacts_close_errors() -> None:
    stream = ClosingStream(RuntimeError("key=croo_sk_close-secret"))

    closed, error = await bounded_close(stream, timeout_seconds=0.1)

    assert closed is False
    assert error is not None
    assert "croo_sk_" not in error
    assert "close-secret" not in error


def test_shared_redaction_hides_credential_websocket_urls() -> None:
    redacted = redact_sensitive_text(
        "failed wss://api.croo.network/ws?key=croo_sk_shared-secret"
    )

    assert redacted == "failed [REDACTED_WEBSOCKET_URL]"
