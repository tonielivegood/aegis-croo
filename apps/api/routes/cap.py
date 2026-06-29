from fastapi import APIRouter, HTTPException

from apps.api.routes.orders import order_ledger
from src.aegis_croo.cap.adapter import CAPAdapter, RealCAPIntegrationPendingError
from src.aegis_croo.cap.models import CAPOrderRequest, CAPOrderResult, REAL_CAP_PENDING_DETAIL


router = APIRouter()
cap_adapter = CAPAdapter(order_ledger)


@router.post("/cap/order", response_model=CAPOrderResult)
def create_cap_order(request: CAPOrderRequest) -> CAPOrderResult:
    try:
        return cap_adapter.create_order(request)
    except RealCAPIntegrationPendingError as exc:
        raise HTTPException(status_code=501, detail=REAL_CAP_PENDING_DETAIL) from exc
