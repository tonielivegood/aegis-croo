from src.aegis_croo.cap.config import configured_cap_mode, load_cap_provider_config
from src.aegis_croo.cap.models import (
    CAPOrderRequest,
    CAPOrderResult,
    CAPStatusResponse,
    MOCK_CAP_STATUS_DISCLAIMER,
    REAL_CAP_CONFIGURED_DISCLAIMER,
    REAL_CAP_MISSING_DISCLAIMER,
)
from src.aegis_croo.orders.ledger import InMemoryOrderLedger
from src.aegis_croo.orders.models import LocalOrderRequest


class CAPAdapter:
    def __init__(self, ledger: InMemoryOrderLedger) -> None:
        self._ledger = ledger

    def create_order(self, request: CAPOrderRequest) -> CAPOrderResult:
        mode = request.cap_mode or configured_cap_mode()
        if mode != "mock":
            raise RealCAPIntegrationPendingError

        local_request = LocalOrderRequest.model_validate(
            request.model_dump(exclude={"cap_mode"})
        )
        local_order = self._ledger.create_order(local_request)
        return CAPOrderResult.from_local_order(local_order)

    def status(self) -> CAPStatusResponse:
        config = load_cap_provider_config()
        if config.cap_mode == "mock":
            return CAPStatusResponse(
                cap_mode="mock",
                real_cap_ready=False,
                adapter_status="MOCK_ONLY",
                sdk_import_status="not_required_in_mock_mode",
                service_id_status="missing_or_not_required",
                credential_status="missing_or_not_required",
                provider_agent_id=config.croo_provider_agent_id,
                disclaimer=MOCK_CAP_STATUS_DISCLAIMER,
            )

        missing = config.missing_real_config
        if missing:
            return CAPStatusResponse(
                cap_mode="real",
                real_cap_ready=False,
                adapter_status="REAL_CAP_PENDING_CREDENTIALS",
                sdk_import_status="not_loaded_in_step_5b",
                service_id_status=(
                    "missing" if "CROO_SERVICE_ID" in missing else "present"
                ),
                credential_status=(
                    "missing" if "CROO_SDK_KEY" in missing else "present"
                ),
                provider_agent_id=config.croo_provider_agent_id,
                disclaimer=REAL_CAP_MISSING_DISCLAIMER,
                missing=missing,
            )

        return CAPStatusResponse(
            cap_mode="real",
            real_cap_ready=False,
            adapter_status="REAL_CAP_CONFIG_PRESENT_PENDING_STEP_6_VERIFICATION",
            sdk_import_status="not_loaded_in_step_5b",
            service_id_status="present",
            credential_status="present",
            provider_agent_id=config.croo_provider_agent_id,
            disclaimer=REAL_CAP_CONFIGURED_DISCLAIMER,
            missing=[],
        )


class RealCAPIntegrationPendingError(Exception):
    pass
