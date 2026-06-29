# A2A Mock Execution Demo Design

## Goal

Add a deterministic mock buyer/execution-agent flow that proves an external
agent can submit a proposed action to Aegis, receive pre-trade risk advice,
and obey that advice without performing a real trade.

## Scope and Safety

Step 3 adds only `POST /a2a/mock-order`, an in-process mock agent, deterministic
tests, one executable example, and one short README command. It does not add
CAP, UI, live providers, portfolio-check endpoints, marketplace documentation,
wallets, keys, signing, swaps, transaction construction, or broadcasting.
BNB/BSC remains a demo fixture behind the chain-neutral `RiskCheckRequest`.

## Architecture

`MockExecutionAgent` accepts a risk-assessor callable through constructor
injection. The default assessor is Step 2's `assess_risk`. Its only public
operation receives a `buyer_agent_id` and `RiskCheckRequest`, calls the assessor
exactly once, and maps the returned advice to a mock-only status:

- `BLOCK` -> `REFUSED`
- `WAIT` -> `DELAYED`
- `EXECUTE` -> `SIMULATED_EXECUTION_ONLY`

The dependency boundary proves that the oracle is consulted before the mock
status is selected and allows isolated tests without network calls. The agent
contains no execution callback or integration point for trading infrastructure.

## API Contract

`POST /a2a/mock-order` accepts:

- `buyer_agent_id`: a non-empty string
- `requested_action`: the existing `RiskCheckRequest`

The response contains exactly:

- `buyer_agent_id`
- `aegis_decision`
- `risk_score`
- `safe_to_execute`
- `mock_execution_status`
- `reason`
- `risk_factors`
- `proof`

The route owns thin Pydantic request/response models and delegates all behavior
to a module-level `MockExecutionAgent`. It does not duplicate risk rules.

## Deterministic Reasons

- `REFUSED`: Aegis blocked the requested action, so mock execution was refused.
- `DELAYED`: Aegis requested more or safer evidence, so mock execution was delayed.
- `SIMULATED_EXECUTION_ONLY`: Aegis allowed the proposed action, but this demo
  only records a simulated outcome and submits nothing.

The response carries the oracle's risk factors and proof unchanged so callers
can explain and verify the decision.

## Example

`examples/mock_buyer_agent_demo.py` sends the documented volatile-buy payload
to a locally running `/a2a/mock-order` endpoint using Python's standard library
and prints the JSON response. It has no chain SDK or execution capability.

## Testing

API tests cover volatile buy -> REFUSED, missing data -> DELAYED, safe small buy
-> SIMULATED_EXECUTION_ONLY, and unknown token -> REFUSED. They assert the full
response shape, risk factors, proof, and safety flag. A focused unit test uses
an injected assessor spy to prove the agent calls Aegis before status mapping.
The complete Step 1/2/3 suite must pass.

## Self-Review

- No placeholders or ambiguous status mappings remain.
- Risk scoring and guard rules stay exclusively in the Step 2 oracle.
- No network self-call, real execution, wallet, signing, or broadcast path exists.
- Every requested response field and acceptance scenario is covered.
- Changes remain within the files authorized for Step 3 plus this design record.
