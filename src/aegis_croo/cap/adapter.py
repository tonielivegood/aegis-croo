from src.aegis_croo.cap.config import configured_cap_mode
from src.aegis_croo.cap.models import CAPOrderRequest, CAPOrderResult
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


class RealCAPIntegrationPendingError(Exception):
    pass
