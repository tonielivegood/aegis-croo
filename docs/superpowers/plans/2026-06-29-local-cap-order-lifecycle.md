# Local CAP-Ready Order Lifecycle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a process-local CAP-shaped Order lifecycle that calls Aegis Risk Check, stores the resulting Order and Delivery Proof, and exposes retrieval endpoints.

**Architecture:** Typed Pydantic models define request/result/proof contracts. A deterministic hashing module builds local proof data, while a thread-safe in-memory ledger orchestrates the four mock lifecycle states and calls the existing risk oracle exactly once; FastAPI routes remain thin adapters.

**Tech Stack:** Python 3.14, FastAPI, Pydantic, pytest, standard-library hashlib/json/threading/uuid/datetime

## Global Constraints

- Implement Step 4 only.
- Add `POST /orders`, `GET /orders/{order_id}`, and `GET /proof/{proof_id}`.
- Lifecycle is exactly `NEGOTIATED_MOCK -> LOCKED_MOCK -> DELIVERED -> CLEARED_MOCK`.
- `cap_mode` is `local_mock` and the required disclaimer is exact.
- Reuse the existing risk oracle; do not duplicate or refactor risk logic.
- Do not add or import CROO SDK.
- Do not add real payment, escrow, settlement, reputation, or on-chain delivery.
- Do not add wallets, private keys, signing, swaps, trading, transaction construction, broadcasting, live providers, or UI.

---

### Task 1: Order Models and Deterministic Proof Hashing

**Files:**
- Create: `src/aegis_croo/orders/__init__.py`
- Create: `src/aegis_croo/orders/models.py`
- Create: `src/aegis_croo/orders/proof.py`
- Create: `tests/test_orders.py`

**Interfaces:**
- Consumes: `RiskCheckRequest`, `RiskCheckResponse`, `RiskFactor`, `Confidence`, `Decision`.
- Produces: `OrderLifecycleStatus`, `LocalOrderRequest`, `LocalDeliveryProof`, `LocalOrderResult`, `canonical_hash(value)`, and `build_delivery_proof(order_id, request_payload, risk_response, created_at, proof_id)`.

- [ ] **Step 1: Write failing model/hash tests**

Create a valid order fixture and assert the models import, lifecycle enum values are exact, required disclaimer/mode validate, hashes are 64-character SHA-256 strings, and two dictionaries with different key order produce the same canonical hash.

- [ ] **Step 2: Verify RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_orders.py -v`
Expected: collection failure because `src.aegis_croo.orders` does not exist.

- [ ] **Step 3: Implement minimal typed contracts and hashing**

Use string enums/Literals for lifecycle and local CAP mode. Serialize hashing inputs with `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=True)` and SHA-256. `build_delivery_proof` hashes the complete order request, complete risk response, and `{ "deliverable_type": "schema", "deliverable": risk_response }`.

- [ ] **Step 4: Verify GREEN**

Run the focused test file and expect all model/hash tests to pass.

- [ ] **Step 5: Commit**

Run `git add src/aegis_croo/orders tests/test_orders.py` and commit `feat: add local order and proof models`.

### Task 2: In-Memory Ledger and Lifecycle Orchestration

**Files:**
- Create: `src/aegis_croo/orders/ledger.py`
- Modify: `src/aegis_croo/orders/__init__.py`
- Modify: `tests/test_orders.py`

**Interfaces:**
- Consumes: `LocalOrderRequest`, `LocalOrderResult`, `LocalDeliveryProof`, `build_delivery_proof`, and `assess_risk`.
- Produces: `InMemoryOrderLedger.create_order`, `get_order`, and `get_proof`.

- [ ] **Step 1: Add failing ledger tests**

Instantiate a fresh ledger, create a volatile order, and assert final status/lifecycle, BLOCK deliverable, stored order/proof equality, unique prefixed identifiers, UTC timestamps, exact disclaimer, and missing lookups returning `None`. Create equivalent orders and assert all three proof hashes match despite different IDs/timestamps.

- [ ] **Step 2: Verify RED**

Run the ledger tests and expect import/attribute failures because the ledger is absent.

- [ ] **Step 3: Implement minimal ledger**

Use process-local dictionaries protected by `threading.RLock`. Generate IDs with `uuid4().hex`, call the injected/default risk assessor exactly once, build proof and result, then store both under one lock. Return `None` for unknown IDs.

- [ ] **Step 4: Verify GREEN**

Run all order tests and expect model/hash/ledger tests to pass.

- [ ] **Step 5: Commit**

Run `git add src/aegis_croo/orders tests/test_orders.py` and commit `feat: add local CAP order ledger`.

### Task 3: Order and Proof API Endpoints

**Files:**
- Create: `apps/api/routes/orders.py`
- Modify: `apps/api/main.py`
- Modify: `tests/test_orders.py`

**Interfaces:**
- Consumes: one module-level `InMemoryOrderLedger` and typed request/result/proof models.
- Produces: `POST /orders`, `GET /orders/{order_id}`, and `GET /proof/{proof_id}`.

- [ ] **Step 1: Add failing API acceptance tests**

Use `TestClient(app)` to verify volatile BLOCK and safe EXECUTE orders, exact response keys/status/lifecycle/mode/disclaimer, GET order/proof equality, required proof keys, 404 for unknown IDs, and absence of forbidden response field names.

- [ ] **Step 2: Verify RED**

Run API order tests. Expected: HTTP 404 because the router is not registered.

- [ ] **Step 3: Implement and register thin routes**

Create one process-local ledger, delegate POST/GET operations, translate missing records to `HTTPException(status_code=404)`, and include the router in `apps/api/main.py`.

- [ ] **Step 4: Verify GREEN and regressions**

Run `tests/test_orders.py`, then `.\.venv\Scripts\python.exe -m pytest -v`; all existing and new tests must pass.

- [ ] **Step 5: Commit**

Run `git add apps/api/routes/orders.py apps/api/main.py tests/test_orders.py` and commit `feat: expose local CAP order endpoints`.

### Task 4: Local Order Demo and Documentation

**Files:**
- Create: `examples/order_flow_demo.py`
- Modify: `README.md`

**Interfaces:**
- Demonstrates: POST local order, GET stored order, and GET local proof using Python standard library only.

- [ ] **Step 1: Add the demo**

Use `urllib.request` and the documented service fixture. Print the three JSON responses without importing chain, wallet, trading, or CROO packages.

- [ ] **Step 2: Update README minimally**

Document local endpoints, lifecycle, in-memory reset limitation, price/SLA fixture, exact CAP disclaimer, and commands for the demo. Explicitly state this is not real CAP payment/escrow/settlement/on-chain delivery.

- [ ] **Step 3: Verify final scope**

Run full pytest, compile new modules/demo, `git diff --check`, scan for `croo-sdk` and forbidden implementation imports/paths, confirm no `.env`, and list changed files from the pre-Step-4 commit.

- [ ] **Step 4: Commit**

Run `git add examples/order_flow_demo.py README.md` and commit `docs: add local CAP order demo`.

## Self-Review

- Every required endpoint, response field, lifecycle status, proof field, hash rule, and test maps to a task.
- IDs/timestamps are excluded from deterministic hash inputs.
- Route, ledger, proof, and model responsibilities are separated without excess abstraction.
- Existing risk and A2A behavior remain untouched.
- No placeholder, real CAP claim, SDK dependency, or prohibited execution capability is included.
