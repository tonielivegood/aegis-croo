# Aegis CROO session handoff - Step 5B complete

## Current repo state

- Repo path: `E:\Aegis-CROO`
- Branch: `main`
- Latest commit: `8ed5cdf feat: add CAP provider readiness status`
- Latest verified pytest result: `55 passed, 1 known Starlette/httpx warning`

Known warning:

- `StarletteDeprecationWarning` from `fastapi.testclient` / `httpx`.

## Implemented endpoints

- `GET /health`
- `POST /risk-check`
- `POST /a2a/mock-order`
- `POST /orders`
- `GET /orders/{order_id}`
- `GET /proof/{proof_id}`
- `GET /cap/status`
- `POST /cap/order`

## Step 1-5B summary

- Step 1: Established the deterministic Aegis Risk Oracle foundation and API shape.
- Step 2: Refactored risk logic into explainable guard-based risk factors.
- Step 3: Added A2A mock requester/execution demo that obeys Aegis decisions.
- Step 3.5: Aligned CROO/CAP terminology and safety wording.
- Step 4: Added local mock CAP-shaped order lifecycle with in-memory ledger and delivery proof.
- Step 5A: Added mock-first CAP adapter boundary via `POST /cap/order`.
- Step 5B: Added CAP SDK-ready provider readiness boundary via `GET /cap/status`.

## Current CAP status

- `CAP_MODE` defaults to `mock`.
- `/cap/order` is mock-first and maps CAP-shaped requests into the existing local in-memory order flow.
- `/cap/status` reports mock or real-mode readiness without exposing secret values.
- Real CAP mode is not verified yet.
- Real mode does not fake success.

Mock mode status:

- Adapter status: `MOCK_ONLY`
- SDK import status: `not_required_in_mock_mode`
- Real CAP ready: `false`

Real mode with missing configuration:

- Adapter status: `REAL_CAP_PENDING_CREDENTIALS`
- Real CAP ready: `false`
- Missing configuration is reported by variable name only.

## Mock vs real

Mock/local only:

- `/orders`
- `/proof/{proof_id}`
- `/cap/order`
- `/cap/status`
- Local delivery proof / log attestation hashes
- In-memory ledger
- Mock CAP lifecycle and local adapter metadata

Not real yet:

- CROO SDK integration
- Real CAP payment
- USDC escrow lock
- Settlement
- Reputation updates
- On-chain delivery
- Real provider verification

## Safety rules

Aegis Risk Oracle is a pre-trade risk oracle, not a trading bot.

Do not add:

- Live trading
- Wallet logic
- Private keys
- Signing
- Swaps
- Transaction construction
- Transaction broadcasting
- Real CAP payment or escrow claims before verification

`EXECUTE` means only that the risk decision says the proposed action is acceptable. It is not transaction authorization.

## CROO Agent Store service info

- Provider Agent: `aegis-risk-oracle`
- Service name: `Aegis Risk Check`
- Service ID: `aegis-risk-check-schema-v1`
- Price: `0.25 USDC`
- SLA: `5 minutes`
- Requirements type: `schema`
- Deliverable type: `schema`
- Deliverable: risk-check JSON response with decision, score, confidence, reasons, risk factors, suggested action, and local proof hashes.

No secrets are stored in this handoff.

## Exact next step

Step 6 only: real CROO provider verification.

Step 6 should verify the provider flow against the real CROO Dashboard/SDK without claiming real payment, escrow, settlement, reputation, or on-chain delivery until observed and proven.

## Required environment variables for Step 6

Set these outside the repo, never commit values:

- `CAP_MODE=real`
- `CROO_API_URL`
- `CROO_WS_URL`
- `CROO_SDK_KEY`
- `CROO_SERVICE_ID`
- `CROO_PROVIDER_AGENT_ID` optional, defaults to `aegis-risk-oracle`

Do not commit `.env` files or secret values.

## Warnings and known limitations

- Tests currently pass without `croo-sdk` installed.
- `croo-sdk` is not imported yet.
- No real CAP network calls are run in local tests.
- Local orders/proofs are stored in memory and disappear when the API restarts.
- Delivery proof is local hash-based proof/log attestation, not on-chain proof.
- Real CAP verification is pending Step 6.

## Local commands

Install dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Run API locally:

```powershell
.\.venv\Scripts\python.exe -m uvicorn apps.api.main:app --reload
```

Check CAP status:

```powershell
curl.exe http://127.0.0.1:8000/cap/status
```
