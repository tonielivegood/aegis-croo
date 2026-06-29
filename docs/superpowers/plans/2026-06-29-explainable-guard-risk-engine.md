# Explainable Guard Risk Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Step 1 monolithic classifier with deterministic, explainable risk guards while preserving the advisory-only API.

**Architecture:** Each guard implements `BaseGuard.evaluate(RiskCheckRequest) -> RiskFactor | None`. The oracle runs an ordered guard registry, sums impacts to a capped score, applies the missing-core-data floor, and derives the response and proof without any execution capability.

**Tech Stack:** Python 3.14, Pydantic, FastAPI, pytest

## Global Constraints

- Implement Step 2 only.
- No CAP, web UI, live providers, portfolio-check endpoint, or marketplace docs.
- No live trading, swaps, wallets, private keys, or transaction broadcasting.
- Keep product logic chain-agnostic; BNB/BSC is only a demo supported-market fixture.
- Decision thresholds: 0-34 EXECUTE, 35-69 WAIT, 70-100 BLOCK.

---

### Task 1: Schema and Guard Contracts

**Files:**
- Modify: `src/aegis_croo/schemas/risk.py`
- Create: `src/aegis_croo/guards/base.py`
- Create: `tests/test_guards.py`

**Interfaces:**
- Produces: `RiskSeverity`, `RiskFactor`, `PortfolioContext`, extended `MarketSignal` and `RiskCheckRequest`, and abstract `BaseGuard.evaluate(request)`.

- [ ] **Step 1: Write failing contract tests**

Add tests that construct the extended request fields, validate a `RiskFactor`, and import `BaseGuard`.

- [ ] **Step 2: Verify RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_guards.py -v`
Expected: collection failure because guard modules/types do not exist.

- [ ] **Step 3: Implement the minimal contracts**

Add severity enum, factor/context models, optional slippage/gas/context fields, response `risk_factors`, and an ABC with `evaluate`.

- [ ] **Step 4: Verify GREEN for contract tests**

Run the focused pytest command and expect the contract tests to pass.

### Task 2: Eight Deterministic Guards

**Files:**
- Create: `src/aegis_croo/guards/__init__.py`
- Create: `src/aegis_croo/guards/volatility_guard.py`
- Create: `src/aegis_croo/guards/liquidity_guard.py`
- Create: `src/aegis_croo/guards/volume_guard.py`
- Create: `src/aegis_croo/guards/exposure_guard.py`
- Create: `src/aegis_croo/guards/slippage_guard.py`
- Create: `src/aegis_croo/guards/gas_guard.py`
- Create: `src/aegis_croo/guards/unknown_token_guard.py`
- Create: `src/aegis_croo/guards/suspicious_pump_guard.py`
- Modify: `tests/test_guards.py`

**Interfaces:**
- Consumes: `BaseGuard`, `RiskCheckRequest`, `RiskFactor`, `RiskSeverity`.
- Produces: one concrete class per guard and ordered `DEFAULT_GUARDS` exports.

- [ ] **Step 1: Add one failing behavior test per threshold band and no-op boundary**

Use real Pydantic requests. Assert factor name, severity, score impact, and evidence for all guards, plus `None` when a rule is not triggered.

- [ ] **Step 2: Verify RED**

Run focused guard tests and confirm imports/expectations fail for missing behavior.

- [ ] **Step 3: Implement minimal guards from the approved scoring table**

Each guard reads only its relevant request fields and returns deterministic evidence. Unsupported markets are supplied through a chain-neutral constructor registry with `{("bsc", "BNB")}` as the demo default.

- [ ] **Step 4: Verify GREEN and refactor exports**

Run all guard tests; then remove duplication without altering behavior and rerun.

### Task 3: Oracle Aggregation and API Scenarios

**Files:**
- Modify: `src/aegis_croo/oracle/risk_oracle.py`
- Modify: `tests/test_risk_check.py`

**Interfaces:**
- Consumes: `DEFAULT_GUARDS` and extended risk schemas.
- Produces: `assess_risk` response containing ordered `risk_factors` and proof hashes.

- [ ] **Step 1: Add failing API tests**

Update response-shape assertion for `risk_factors`; assert volatile buy BLOCK, safe buy EXECUTE, missing data WAIT/low confidence, unknown market BLOCK, high slippage BLOCK, suspicious pump BLOCK, and overexposure not EXECUTE.

- [ ] **Step 2: Verify RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_risk_check.py -v`
Expected: failures because the old oracle omits risk factors and new aggregation/regimes.

- [ ] **Step 3: Implement minimal aggregation**

Run guards in order, cap summed impacts at 100, floor incomplete core data at 35, derive decision/confidence/regime/action/reasons, and include serialized factors in response proof hashing.

- [ ] **Step 4: Verify GREEN and full regression suite**

Run risk API tests, then all pytest tests. Fix production code for any failures without weakening requirements.

### Task 4: Documentation and Scope Verification

**Files:**
- Modify: `README.md`

**Interfaces:**
- Documents: `risk_factors` response field and guard-based advisory behavior.

- [ ] **Step 1: Make the minimal README update**

State that factors contain name, severity, score impact, and evidence; preserve explicit non-trading safety language.

- [ ] **Step 2: Run final verification**

Run `.\.venv\Scripts\python.exe -m pytest -v` and inspect `rg` results for wallet/private-key/swap/broadcast/live-provider code.

- [ ] **Step 3: Report evidence**

Print the changed-file list, exact pytest summary, and limitations. Note that Git-based diff/commit reporting is unavailable because the workspace is not a Git repository.

## Self-Review

- Every approved guard and acceptance scenario maps to a task and focused test.
- Interfaces and field names match the approved design.
- No placeholder or unrelated subsystem is included.
