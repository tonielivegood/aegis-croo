from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.aegis_croo.agents.mock_execution_agent import (
    MockExecutionAgent,
    MockOrderResult,
)
from src.aegis_croo.schemas.risk import RiskCheckRequest


router = APIRouter()
mock_execution_agent = MockExecutionAgent()


class MockOrderRequest(BaseModel):
    buyer_agent_id: str = Field(min_length=1)
    requested_action: RiskCheckRequest


@router.post("/a2a/mock-order", response_model=MockOrderResult)
def mock_order(request: MockOrderRequest) -> MockOrderResult:
    return mock_execution_agent.process_order(
        request.buyer_agent_id,
        request.requested_action,
    )
