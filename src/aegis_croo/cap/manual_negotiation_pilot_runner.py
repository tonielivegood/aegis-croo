from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from src.aegis_croo.cap.controlled_provider_runtime import SanitizedRuntimeEvent
from src.aegis_croo.cap.gated_real_sdk_adapter import (
    CredentialsProvider,
    GatedRealCROOSDKAdapter,
    ModuleImporter,
    RealSDKGateSnapshot,
)
from src.aegis_croo.cap.option_b_pilot_runner import (
    OptionBNegotiationPilotRequest,
    OptionBNegotiationPilotRunner,
)
from src.aegis_croo.cap.pilot_readiness import PilotRunIDLookup
from src.aegis_croo.cap.quarantined_sdk_connector import (
    QuarantinedConnectorRequest,
    QuarantinedConnectorStatus,
    QuarantinedSDKNegotiationConnector,
)
from src.aegis_croo.cap.ws_safety import redact_sensitive_text


class ManualNegotiationPilotRequest(BaseModel):
    pilot: OptionBNegotiationPilotRequest = Field(
        default_factory=OptionBNegotiationPilotRequest
    )
    sdk_gates: RealSDKGateSnapshot = Field(default_factory=RealSDKGateSnapshot)
    manual_operator_approval: bool = False
    max_events: int = 0


class ManualNegotiationPilotResult(BaseModel):
    status: QuarantinedConnectorStatus
    reason_codes: list[str] = Field(default_factory=list)
    negotiation_evidence: SanitizedRuntimeEvent | None = None
    event_received: bool = False
    close_attempted: bool = False
    closed: bool = False
    local_only: Literal[True] = True
    manual_review_only: Literal[True] = True
    live_execution_authorized: Literal[False] = False
    mutating_methods_called: Literal[False] = False
    real_cap_ready: Literal[False] = False
    error: str | None = None


class ManualRealNegotiationPilotRunner:
    """Explicit, disabled-by-default Option B operator boundary."""

    def __init__(
        self,
        *,
        credentials_provider: CredentialsProvider,
        importer: ModuleImporter | None = None,
    ) -> None:
        self._credentials_provider = credentials_provider
        self._importer = importer

    async def run_once(
        self,
        request: ManualNegotiationPilotRequest,
        *,
        run_registry: PilotRunIDLookup | None = None,
    ) -> ManualNegotiationPilotResult:
        reasons = _manual_gate_failures(request)
        if reasons:
            return ManualNegotiationPilotResult(
                status="no_go",
                reason_codes=reasons,
            )

        adapter = GatedRealCROOSDKAdapter(
            gates=request.sdk_gates,
            credentials_provider=self._credentials_provider,
            importer=self._importer,
        )
        connector = QuarantinedSDKNegotiationConnector(
            sdk_loader=adapter.load_client,
            runner=OptionBNegotiationPilotRunner(),
        )
        connector_result = await connector.run(
            QuarantinedConnectorRequest(
                pilot=request.pilot,
                sdk_load_authorized=request.sdk_gates.sdk_load_authorized,
            ),
            run_registry=run_registry,
        )
        evidence = (
            connector_result.runner_result.simulated_event
            if connector_result.runner_result is not None
            else None
        )
        return ManualNegotiationPilotResult(
            status=connector_result.status,
            reason_codes=list(connector_result.reason_codes),
            negotiation_evidence=evidence,
            event_received=connector_result.event_received,
            close_attempted=connector_result.close_attempted,
            closed=connector_result.closed,
            error=(
                redact_sensitive_text(connector_result.error)
                if connector_result.error
                else None
            ),
        )


def _manual_gate_failures(
    request: ManualNegotiationPilotRequest,
) -> list[str]:
    gates = request.sdk_gates
    reasons: list[str] = []
    if gates.cap_mode != "real":
        reasons.append("real_mode_required")
    if not gates.cap_pilot_enabled:
        reasons.append("master_pilot_gate_disabled")
    if not gates.connector_start_authorized:
        reasons.append("connector_start_not_authorized")
    if not gates.sdk_load_authorized:
        reasons.append("sdk_load_not_authorized")
    if not gates.option_b_negotiation_pilot_authorized:
        reasons.append("option_b_pilot_not_authorized")
    if not request.manual_operator_approval:
        reasons.append("manual_operator_approval_required")
    if request.max_events != 1:
        reasons.append("event_limit_invalid")
    if gates.require_fund_transfer:
        reasons.append("fund_transfer_enabled")
    if any(
        (
            gates.accept_enabled,
            gates.reject_enabled,
            gates.pay_enabled,
            gates.deliver_enabled,
            gates.upload_enabled,
            gates.settle_enabled,
            gates.clear_enabled,
        )
    ):
        reasons.append("mutation_gate_enabled")
    return list(dict.fromkeys(reasons))
