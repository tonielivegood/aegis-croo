import pytest

from src.aegis_croo.cap.config import (
    CAP_CONTROLLED_PROVIDER_RUNTIME_ENABLED,
    CAP_PROVIDER_ACCEPT_ENABLED,
    CAP_PROVIDER_DELIVER_ENABLED,
    CAP_PROVIDER_PAID_ORDER_HANDLING_ENABLED,
    CAP_PROVIDER_REJECT_ENABLED,
    CAP_PROVIDER_RUNTIME_CLOSE_TIMEOUT_SECONDS,
    CAP_PROVIDER_RUNTIME_MAX_EVENTS,
    CAP_PROVIDER_RUNTIME_TIMEOUT_SECONDS,
    load_controlled_provider_runtime_config,
)


RUNTIME_ENV = (
    "CAP_CONTROLLED_PROVIDER_RUNTIME_ENABLED",
    "CAP_PROVIDER_ACCEPT_ENABLED",
    "CAP_PROVIDER_REJECT_ENABLED",
    "CAP_PROVIDER_PAID_ORDER_HANDLING_ENABLED",
    "CAP_PROVIDER_DELIVER_ENABLED",
    "CAP_PROVIDER_RUNTIME_TIMEOUT_SECONDS",
    "CAP_PROVIDER_RUNTIME_CLOSE_TIMEOUT_SECONDS",
    "CAP_PROVIDER_RUNTIME_MAX_EVENTS",
)


def test_controlled_runtime_configuration_is_disabled_and_bounded_by_default(
    monkeypatch,
) -> None:
    for name in RUNTIME_ENV:
        monkeypatch.delenv(name, raising=False)

    config = load_controlled_provider_runtime_config()

    assert CAP_CONTROLLED_PROVIDER_RUNTIME_ENABLED is False
    assert CAP_PROVIDER_ACCEPT_ENABLED is False
    assert CAP_PROVIDER_REJECT_ENABLED is False
    assert CAP_PROVIDER_PAID_ORDER_HANDLING_ENABLED is False
    assert CAP_PROVIDER_DELIVER_ENABLED is False
    assert CAP_PROVIDER_RUNTIME_TIMEOUT_SECONDS == 5.0
    assert CAP_PROVIDER_RUNTIME_CLOSE_TIMEOUT_SECONDS == 1.0
    assert CAP_PROVIDER_RUNTIME_MAX_EVENTS == 2
    assert config.runtime_enabled is False
    assert config.accept_enabled is False
    assert config.reject_enabled is False
    assert config.paid_order_handling_enabled is False
    assert config.deliver_enabled is False
    assert config.timeout_seconds == 5.0
    assert config.close_timeout_seconds == 1.0
    assert config.max_events == 2


@pytest.mark.parametrize("bad_value", ["", "zero", "0", "-1", "61"])
def test_controlled_runtime_invalid_bounds_fall_back_to_safe_defaults(
    monkeypatch,
    bad_value: str,
) -> None:
    monkeypatch.setenv("CAP_PROVIDER_RUNTIME_TIMEOUT_SECONDS", bad_value)
    monkeypatch.setenv("CAP_PROVIDER_RUNTIME_CLOSE_TIMEOUT_SECONDS", bad_value)
    monkeypatch.setenv("CAP_PROVIDER_RUNTIME_MAX_EVENTS", bad_value)

    config = load_controlled_provider_runtime_config()

    assert config.timeout_seconds == CAP_PROVIDER_RUNTIME_TIMEOUT_SECONDS
    assert config.close_timeout_seconds == CAP_PROVIDER_RUNTIME_CLOSE_TIMEOUT_SECONDS
    assert config.max_events == CAP_PROVIDER_RUNTIME_MAX_EVENTS


def test_controlled_runtime_action_gates_are_independent(monkeypatch) -> None:
    for name in RUNTIME_ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("CAP_PROVIDER_ACCEPT_ENABLED", "true")

    config = load_controlled_provider_runtime_config()

    assert config.runtime_enabled is False
    assert config.accept_enabled is True
    assert config.reject_enabled is False
    assert config.paid_order_handling_enabled is False
    assert config.deliver_enabled is False
