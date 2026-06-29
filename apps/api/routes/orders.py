from fastapi import APIRouter, HTTPException

from src.aegis_croo.orders.ledger import InMemoryOrderLedger
from src.aegis_croo.orders.models import (
    LocalDeliveryProof,
    LocalOrderRequest,
    LocalOrderResult,
)


router = APIRouter()
order_ledger = InMemoryOrderLedger()


@router.post("/orders", response_model=LocalOrderResult)
def create_order(request: LocalOrderRequest) -> LocalOrderResult:
    return order_ledger.create_order(request)


@router.get("/orders/{order_id}", response_model=LocalOrderResult)
def get_order(order_id: str) -> LocalOrderResult:
    order = order_ledger.get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Local mock order not found.")
    return order


@router.get("/proof/{proof_id}", response_model=LocalDeliveryProof)
def get_proof(proof_id: str) -> LocalDeliveryProof:
    proof = order_ledger.get_proof(proof_id)
    if proof is None:
        raise HTTPException(status_code=404, detail="Local delivery proof not found.")
    return proof
