from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field

from src.aegis_croo.cap.config import (
    ControlledProviderRuntimeConfig,
    load_controlled_provider_runtime_config,
)
from src.aegis_croo.cap.provider_adapter import (
    CAPProviderActionPlan,
    plan_from_guard_result,
)
from src.aegis_croo.cap.provider_guard import (
    CAPProviderGuardResult,
    GuardDecision,
    evaluate_cap_provider_guard,
)
from src.aegis_croo.cap.ws_safety import bounded_close, redact_sensitive_text
from src.aegis_croo.oracle.risk_oracle import assess_risk
from src.aegis_croo.schemas.risk import RiskCheckRequest, RiskCheckResponse


RuntimeStatus = Literal[
    "completed",
    "timed_out",
    "manual_review",
    "error",
    "close_failed",
    "event_limit_reached",
]
RuntimeAction = Literal[
    "accept_authorized_test",
    "would_reject",
    "would_manual_review",
    "would_deliver_schema",
]


class ControlledProviderStream(Protocol):
    def on_any(self, handler: Callable[[Any], None]) -> None: ...

    async def close(self) -> None: ...


RuntimeConnector = Callable[[ControlledProviderStream], Awaitable[None]]
GuardEvaluator = Callable[[dict[str, Any]], CAPProviderGuardResult]
Planner = Callable[[CAPProviderGuardResult], CAPProviderActionPlan]
RiskAssessor = Callable[[RiskCheckRequest], RiskCheckResponse]


class SanitizedRuntimeEvent(BaseModel):
    event_type: str
    has_negotiation_id: bool
    has_order_id: bool


class ProviderRuntimeDirective(BaseModel):
    event: SanitizedRuntimeEvent
    action: RuntimeAction
    guard_decision: GuardDecision | None = None
    reason_codes: list[str] = Field(default_factory=list)
    deliverable_type: Literal["schema"] | None = None
    deliverable: RiskCheckResponse | None = None


class ControlledProviderRuntimeResult(BaseModel):
    status: RuntimeStatus
    local_only: Literal[True] = True
    real_action_performed: Literal[False] = False
    real_cap_ready: Literal[False] = False
    close_attempted: Literal[True] = True
    connected: bool
    closed: bool
    events_processed: int
    directives: list[ProviderRuntimeDirective] = Field(default_factory=list)
    error: str | None = None


class ControlledProviderRuntimeDisabledError(RuntimeError):
    pass


class ControlledProviderRuntime:
    """Process injected provider events without any real CAP action surface."""

    def __init__(
        self,
        *,
        config: ControlledProviderRuntimeConfig,
        guard_evaluator: GuardEvaluator = evaluate_cap_provider_guard,
        planner: Planner = plan_from_guard_result,
        risk_assessor: RiskAssessor = assess_risk,
    ) -> None:
        self._config = config
        self._guard_evaluator = guard_evaluator
        self._planner = planner
        self._risk_assessor = risk_assessor

    @classmethod
    def from_environment(cls) -> "ControlledProviderRuntime":
        return cls(config=load_controlled_provider_runtime_config())

    async def run(
        self,
        stream: ControlledProviderStream,
        connect: RuntimeConnector,
    ) -> ControlledProviderRuntimeResult:
        if not self._config.runtime_enabled:
            raise ControlledProviderRuntimeDisabledError(
                "Controlled provider runtime is disabled."
            )

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[Any] = asyncio.Queue()

        def on_event(event: Any) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, event)

        connect_task: asyncio.Task[None] | None = None
        deadline = loop.time() + self._config.timeout_seconds
        approved: dict[str, dict[str, Any]] = {}
        seen: set[tuple[str, str, str]] = set()
        directives: list[ProviderRuntimeDirective] = []
        events_processed = 0
        status: RuntimeStatus = "timed_out"
        error: str | None = None

        try:
            stream.on_any(on_event)
            connect_task = asyncio.create_task(connect(stream))
            while True:
                health_error = _stream_health_error(stream)
                if health_error is not None:
                    status = "error"
                    error = health_error
                    break

                if connect_task.done():
                    connector_error = _task_error(connect_task)
                    if connector_error is not None:
                        status = "error"
                        error = connector_error
                        break

                remaining = deadline - loop.time()
                if remaining <= 0:
                    status = "timed_out"
                    break

                try:
                    event = await asyncio.wait_for(
                        queue.get(), timeout=min(0.01, remaining)
                    )
                except TimeoutError:
                    continue

                events_processed += 1
                directive, terminal_status = self._handle_event(
                    event,
                    approved=approved,
                    seen=seen,
                )
                directives.append(directive)
                if terminal_status is not None:
                    status = terminal_status
                    break
                if events_processed >= self._config.max_events:
                    status = "event_limit_reached"
                    break
        except Exception as exc:
            status = "error"
            error = redact_sensitive_text(str(exc))
        finally:
            if connect_task is not None and not connect_task.done():
                connect_task.cancel()
                await asyncio.gather(connect_task, return_exceptions=True)

        connected = (
            connect_task is not None
            and connect_task.done()
            and not connect_task.cancelled()
            and connect_task.exception() is None
        )
        closed, close_error = await bounded_close(
            stream,
            timeout_seconds=self._config.close_timeout_seconds,
        )
        if not closed:
            status = "close_failed"
            error = close_error

        return ControlledProviderRuntimeResult(
            status=status,
            connected=connected,
            closed=closed,
            events_processed=events_processed,
            directives=directives,
            error=error,
        )

    def _handle_event(
        self,
        event: Any,
        *,
        approved: dict[str, dict[str, Any]],
        seen: set[tuple[str, str, str]],
    ) -> tuple[ProviderRuntimeDirective, RuntimeStatus | None]:
        payload = _event_payload(event)
        summary = _sanitize_event(payload)
        event_key = (
            summary.event_type,
            str(payload.get("negotiation_id") or ""),
            str(payload.get("order_id") or ""),
        )
        if event_key in seen:
            return _manual_review(summary, "duplicate_event"), "manual_review"
        seen.add(event_key)

        if summary.event_type == "order_negotiation_created":
            return self._handle_negotiation(payload, summary, approved)
        if summary.event_type == "order_paid":
            return self._handle_paid(payload, summary, approved)
        return _manual_review(summary, "unknown_event_type"), "manual_review"

    def _handle_negotiation(
        self,
        payload: dict[str, Any],
        summary: SanitizedRuntimeEvent,
        approved: dict[str, dict[str, Any]],
    ) -> tuple[ProviderRuntimeDirective, RuntimeStatus | None]:
        guard_result = self._guard_evaluator(payload)
        plan = self._planner(guard_result)
        if plan.guard_decision == "reject":
            if not self._config.reject_enabled:
                return _manual_review(
                    summary,
                    "reject_gate_disabled",
                    guard_result,
                ), "manual_review"
            return ProviderRuntimeDirective(
                event=summary,
                action="would_reject",
                guard_decision=guard_result.decision,
                reason_codes=guard_result.reason_codes,
            ), "completed"
        if plan.guard_decision == "manual_review":
            return ProviderRuntimeDirective(
                event=summary,
                action="would_manual_review",
                guard_decision=guard_result.decision,
                reason_codes=guard_result.reason_codes,
            ), "manual_review"
        if not self._config.accept_enabled:
            return _manual_review(
                summary,
                "accept_gate_disabled",
                guard_result,
            ), "manual_review"

        negotiation_id = str(payload.get("negotiation_id") or "")
        if not negotiation_id:
            return _manual_review(
                summary,
                "missing_negotiation_id",
                guard_result,
            ), "manual_review"
        approved[negotiation_id] = payload
        directive = ProviderRuntimeDirective(
            event=summary,
            action="accept_authorized_test",
            guard_decision=guard_result.decision,
            reason_codes=guard_result.reason_codes,
        )
        if not self._config.paid_order_handling_enabled:
            return directive, "completed"
        return directive, None

    def _handle_paid(
        self,
        payload: dict[str, Any],
        summary: SanitizedRuntimeEvent,
        approved: dict[str, dict[str, Any]],
    ) -> tuple[ProviderRuntimeDirective, RuntimeStatus]:
        if not self._config.paid_order_handling_enabled:
            return _manual_review(
                summary, "paid_order_handling_gate_disabled"
            ), "manual_review"
        if not self._config.deliver_enabled:
            return _manual_review(
                summary, "deliver_gate_disabled"
            ), "manual_review"

        if not payload.get("order_id"):
            return _manual_review(
                summary, "missing_order_id"
            ), "manual_review"

        negotiation_id = str(payload.get("negotiation_id") or "")
        stored = approved.get(negotiation_id)
        if stored is None:
            return _manual_review(
                summary, "uncorrelated_paid_order"
            ), "manual_review"
        if (
            "requirements" in payload
            and payload["requirements"] != stored.get("requirements")
        ):
            return _manual_review(
                summary, "conflicting_paid_order"
            ), "manual_review"

        guard_result = self._guard_evaluator(stored)
        if guard_result.decision != "accept_candidate":
            return _manual_review(
                summary,
                "guard_recheck_failed",
                guard_result,
            ), "manual_review"

        request = RiskCheckRequest.model_validate(stored.get("requirements"))
        deliverable = RiskCheckResponse.model_validate(
            self._risk_assessor(request)
        )
        return ProviderRuntimeDirective(
            event=summary,
            action="would_deliver_schema",
            guard_decision=guard_result.decision,
            reason_codes=guard_result.reason_codes,
            deliverable_type="schema",
            deliverable=deliverable,
        ), "completed"


def _manual_review(
    event: SanitizedRuntimeEvent,
    reason_code: str,
    guard_result: CAPProviderGuardResult | None = None,
) -> ProviderRuntimeDirective:
    reason_codes = list(guard_result.reason_codes) if guard_result else []
    reason_codes.append(reason_code)
    return ProviderRuntimeDirective(
        event=event,
        action="would_manual_review",
        guard_decision=guard_result.decision if guard_result else None,
        reason_codes=list(dict.fromkeys(reason_codes)),
    )


def _event_payload(event: Any) -> dict[str, Any]:
    if isinstance(event, Mapping):
        return dict(event)
    values = getattr(event, "__dict__", None)
    return dict(values) if isinstance(values, Mapping) else {}


def _sanitize_event(payload: Mapping[str, Any]) -> SanitizedRuntimeEvent:
    raw_type = str(payload.get("type") or "")
    event_type = (
        raw_type
        if raw_type in {"order_negotiation_created", "order_paid"}
        else "unknown_event"
    )
    return SanitizedRuntimeEvent(
        event_type=event_type,
        has_negotiation_id=bool(payload.get("negotiation_id")),
        has_order_id=bool(payload.get("order_id")),
    )


def _stream_health_error(stream: ControlledProviderStream) -> str | None:
    if bool(getattr(stream, "reconnecting", False)):
        return "reconnect_detected"
    error_reader = getattr(stream, "err", None)
    if callable(error_reader):
        error = error_reader()
        if error is not None:
            return redact_sensitive_text(str(error))
    return None


def _task_error(task: asyncio.Task[None]) -> str | None:
    if task.cancelled():
        return "connector_cancelled"
    error = task.exception()
    return redact_sensitive_text(str(error)) if error is not None else None
