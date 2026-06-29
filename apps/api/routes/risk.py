from fastapi import APIRouter

from src.aegis_croo.oracle.risk_oracle import assess_risk
from src.aegis_croo.schemas.risk import RiskCheckRequest, RiskCheckResponse


router = APIRouter()


@router.post("/risk-check", response_model=RiskCheckResponse)
def risk_check(request: RiskCheckRequest) -> RiskCheckResponse:
    return assess_risk(request)
