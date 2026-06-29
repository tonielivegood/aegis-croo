from collections.abc import Callable
from enum import StrEnum

from pydantic import BaseModel, Field

from src.aegis_croo.oracle.risk_oracle import assess_risk
from src.aegis_croo.schemas.common import Decision
from src.aegis_croo.schemas.risk import (
    Proof,
    RiskCheckRequest,
    RiskCheckResponse,
    RiskFactor,
)


RiskAssessor = Callable[[RiskCheckRequest], RiskCheckResponse]


class MockExecutionStatus(StrEnum):
    REFUSED = "REFUSED"
    DELAYED = "DELAYED"
    SIMULATED_EXECUTION_ONLY = "SIMULATED_EXECUTION_ONLY"


class MockOrderResult(BaseModel):
    buyer_agent_id: str = Field(min_length=1)
    aegis_decision: Decision
    risk_score: int = Field(ge=0, le=100)
    safe_to_execute: bool
    mock_execution_status: MockExecutionStatus
    reason: str = Field(min_length=1)
    risk_factors: list[RiskFactor]
    proof: Proof


STATUS_BY_DECISION = {
    Decision.BLOCK: MockExecutionStatus.REFUSED,
    Decision.WAIT: MockExecutionStatus.DELAYED,
    Decision.EXECUTE: MockExecutionStatus.SIMULATED_EXECUTION_ONLY,
}

REASON_BY_STATUS = {
    MockExecutionStatus.REFUSED: (
        "Aegis blocked the requested action, so mock execution was refused."
    ),
    MockExecutionStatus.DELAYED: (
        "Aegis requested more or safer evidence, so mock execution was delayed."
    ),
    MockExecutionStatus.SIMULATED_EXECUTION_ONLY: (
        "Aegis allowed the proposed action, but this demo records only a "
        "simulated outcome and submits nothing."
    ),
}


class MockExecutionAgent:
    def __init__(self, risk_assessor: RiskAssessor = assess_risk) -> None:
        self._risk_assessor = risk_assessor

    def process_order(
        self,
        buyer_agent_id: str,
        requested_action: RiskCheckRequest,
    ) -> MockOrderResult:
        risk = self._risk_assessor(requested_action)
        status = STATUS_BY_DECISION[risk.decision]
        return MockOrderResult(
            buyer_agent_id=buyer_agent_id,
            aegis_decision=risk.decision,
            risk_score=risk.risk_score,
            safe_to_execute=risk.safe_to_execute,
            mock_execution_status=status,
            reason=REASON_BY_STATUS[status],
            risk_factors=risk.risk_factors,
            proof=risk.proof,
        )
