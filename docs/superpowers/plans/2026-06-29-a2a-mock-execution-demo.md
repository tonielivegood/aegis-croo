# A2A Mock Execution Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a mock A2A buyer-agent endpoint that always consults Aegis and maps its advice to a non-executing deterministic status.

**Architecture:** `MockExecutionAgent` receives an injected risk assessor, calls it exactly once, and returns a typed projection of the oracle response. A thin FastAPI route validates the nested Step 2 request and delegates to the agent; no risk rules or execution capabilities are duplicated.

**Tech Stack:** Python 3.14, Pydantic, FastAPI, pytest

## Global Constraints

- Implement Step 3 only.
- Add `POST /a2a/mock-order` and `MockExecutionAgent`.
- Map BLOCK to REFUSED, WAIT to DELAYED, and EXECUTE to SIMULATED_EXECUTION_ONLY.
- BNB/BSC remains a demo fixture, not a product limitation.
- No CAP, web UI, live providers, portfolio-check endpoint, or marketplace docs.
- No trading, swaps, wallet logic, private keys, signing, transaction construction, or broadcasting.

---

### Task 1: Mock Agent Contract and Decision Mapping

**Files:**
- Create: `src/aegis_croo/agents/__init__.py`
- Create: `src/aegis_croo/agents/mock_execution_agent.py`
- Create: `tests/test_a2a_mock_order.py`

**Interfaces:**
- Consumes: `Callable[[RiskCheckRequest], RiskCheckResponse]`, defaulting to `assess_risk`.
- Produces: `MockExecutionStatus`, `MockOrderResult`, and `MockExecutionAgent.process_order(buyer_agent_id, requested_action)`.

- [ ] **Step 1: Write the failing agent unit test**

Create a spy assessor returning a typed WAIT response, call `process_order`, and assert the spy received the exact request before the result reports `DELAYED`. Add parametrized assertions for BLOCK/WAIT/EXECUTE mappings.

- [ ] **Step 2: Verify RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_a2a_mock_order.py -v`
Expected: collection failure because `src.aegis_croo.agents` does not exist.

- [ ] **Step 3: Implement the minimal typed agent**

Define a string enum with exactly the three statuses, a Pydantic result with the eight response fields, deterministic reason strings, and one `process_order` method that calls the assessor before mapping `Decision`.

- [ ] **Step 4: Verify GREEN**

Run the focused test and expect all agent-level mapping tests to pass.

- [ ] **Step 5: Commit**

Run `git add src/aegis_croo/agents tests/test_a2a_mock_order.py` and commit `feat: add mock execution agent`.

### Task 2: A2A API Route

**Files:**
- Create: `apps/api/routes/a2a.py`
- Modify: `apps/api/main.py`
- Modify: `tests/test_a2a_mock_order.py`

**Interfaces:**
- Consumes: `RiskCheckRequest`, `MockExecutionAgent`, and `MockOrderResult`.
- Produces: `MockOrderRequest` and `POST /a2a/mock-order` with `MockOrderResult` response model.

- [ ] **Step 1: Add failing API scenario tests**

Use `TestClient(app)` for volatile buy -> REFUSED, missing liquidity -> DELAYED, safe small buy -> SIMULATED_EXECUTION_ONLY, and unknown token -> REFUSED. Assert exact response keys, proof keys, factor shape, score band, and safety flag.

- [ ] **Step 2: Verify RED**

Run the focused file. Expected: HTTP 404 because the route is not registered.

- [ ] **Step 3: Implement and register the thin route**

Define a request model containing non-empty `buyer_agent_id` and `requested_action: RiskCheckRequest`; instantiate one mock agent; delegate the route handler; include its router in `apps/api/main.py`.

- [ ] **Step 4: Verify GREEN and regressions**

Run the focused test, then `.\.venv\Scripts\python.exe -m pytest -v`; all existing and new tests must pass.

- [ ] **Step 5: Commit**

Run `git add apps/api/routes/a2a.py apps/api/main.py tests/test_a2a_mock_order.py` and commit `feat: expose A2A mock order endpoint`.

### Task 3: Demo and Minimal Documentation

**Files:**
- Create: `examples/mock_buyer_agent_demo.py`
- Modify: `README.md`

**Interfaces:**
- Demonstrates: a standard-library POST to `http://127.0.0.1:8000/a2a/mock-order`.

- [ ] **Step 1: Add the demo script**

Build the volatile-buy request as a Python dictionary, encode it with `json`, send it with `urllib.request`, and print the parsed response. Do not import a chain SDK or expose an execution function.

- [ ] **Step 2: Add one README command**

Document `python examples/mock_buyer_agent_demo.py` after starting the API and state that the result is simulation-only.

- [ ] **Step 3: Verify scope and tests**

Run the full pytest suite, `git diff --check`, a source scan for prohibited execution concepts, and confirm no `.env` file exists.

- [ ] **Step 4: Commit**

Run `git add examples/mock_buyer_agent_demo.py README.md` and commit `docs: add A2A mock buyer demo`.

## Self-Review

- Every approved response field and scenario maps to a focused assertion.
- The assessor dependency and method names are consistent across all tasks.
- The route contains no risk scoring or status logic.
- The example cannot trade or sign anything.
- No placeholder, unrelated subsystem, or deferred Step 3 decision remains.
