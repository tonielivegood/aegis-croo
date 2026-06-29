# Aegis Risk Oracle CROO

Aegis Risk Oracle is a callable, chain-agnostic pre-trade risk oracle for CROO Agent Commerce. As a callable risk-check Service, it evaluates a proposed action before any separately controlled action occurs and returns `BLOCK`, `WAIT`, or `EXECUTE`, along with a deterministic risk score and proof hashes.

It is not a trading bot. Aegis evaluates risk but has no wallet logic, private-key handling, signing, transaction construction, swap endpoint, or broadcast path. BNB on BSC is only a deterministic demo fixture; the request and oracle boundaries remain chain-agnostic for future provider coverage.

## CROO/CAP terminology alignment

In CROO Agent Protocol (CAP) terms, Aegis Risk Oracle is the **Provider Agent** and Aegis Risk Check is its callable **Service**. The risk-check input is the **Requirements** schema, while the risk-check JSON response is the **Deliverable** schema. The A2A mock buyer is the **Requester Agent**; `buyer_agent_id` identifies that requester in this demo.

The `proof` hashes are a local **Delivery Proof / Log Attestation** for the risk-check result. They are not on-chain proof. Real CAP integration is pending: this project does not yet invoke the CROO SDK, real payment, USDC escrow, settlement, reputation updates, or on-chain delivery.

`EXECUTE` means only that the risk decision found the proposed action acceptable. `safe_to_execute` is risk advice, not transaction authorization; Aegis never executes or submits a transaction.

## Quickstart

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest
python -m uvicorn apps.api.main:app --reload
```

The API is available at `http://127.0.0.1:8000`.

## API examples

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Risk check:

```powershell
$body = Get-Content -Raw .\examples\sample_requests.json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/risk-check -ContentType application/json -Body $body
```

Example risk request:

```json
{
  "token": "BNB",
  "chain": "bsc",
  "intended_action": "buy",
  "size_usd": 100,
  "market_signal": {
    "price_change_24h": -8.0,
    "volume_change_24h": -10.0,
    "liquidity_usd": 50000,
    "volatility_24h": 9.0
  }
}
```

The response contains `decision`, `risk_score`, `confidence`, `market_regime`, `safe_to_execute`, `risk_factors`, `reasons`, `suggested_action`, and a `proof` object with request, response, and policy hashes/version data.

## A2A mock requester demo

With the API running, call the simulation-only Requester Agent:

```powershell
python examples/mock_buyer_agent_demo.py
```

The mock Requester Agent maps `BLOCK` to `REFUSED`, `WAIT` to `DELAYED`, and `EXECUTE` to `SIMULATED_EXECUTION_ONLY`; it never submits a trade.

## Local CAP-ready Order demo

Step 4 exposes a process-local CAP-shaped lifecycle:

- `POST /orders`
- `GET /orders/{order_id}`
- `GET /proof/{proof_id}`

The local lifecycle is `NEGOTIATED_MOCK -> LOCKED_MOCK -> DELIVERED -> CLEARED_MOCK`. The demo Service fixture costs 0.25 USDC with a 5-minute SLA, but no payment is made or locked. Run the full local flow with:

```powershell
python examples/order_flow_demo.py
```

Orders and proofs are held only in memory and disappear when the API restarts. `Local mock ledger only. No real CAP payment, escrow, on-chain delivery, or settlement.`

## CAP Adapter Boundary — Mock First

Step 5A exposes `POST /cap/order` as a local mock adapter boundary. It accepts a CAP-shaped order request, maps it into the existing local `/orders` flow, and returns CAP adapter metadata such as `cap_mode: "mock"`, `cap_adapter_status: "CAP_READY_LOCAL_MOCK"`, and the mock CAP lifecycle `NEGOTIATE_MOCK -> LOCK_MOCK -> DELIVER_LOCAL -> CLEAR_MOCK`.

This adapter does not use the real CROO SDK yet. It does not perform real payment, escrow, settlement, reputation, or on-chain delivery. Real CROO provider verification is reserved for Step 6.

## Real CAP readiness

Step 5B adds configuration and status boundaries only. `GET /cap/status` reports whether the mock adapter is active or whether real CAP mode is missing required provider configuration. Local tests do not use real CROO credentials, do not require the CROO SDK, and do not run real CAP network calls.

Step 6B-minimal adds a safe real-mode SDK readiness probe for `GET /cap/status`: when real-mode configuration is present, it can verify only that the CROO SDK import and `AgentClient` initialization path are available. It does not verify real provider readiness, create or deliver orders, perform payment, lock escrow, settle, clear, upload files, update reputation, or submit on-chain delivery. Because the verified CROO Python SDK contract does not expose an official provider/service lookup or auth/status method, `real_cap_ready` remains `false` until official read-only verification or dashboard confirmation is added.

If real CROO credentials are used later, keep them outside the repo in the runtime environment. Do not commit `.env` files or secret values. Real payment, escrow, settlement, reputation, or on-chain delivery must not be claimed until Step 6 verifies them through the CROO Dashboard and SDK.

## Safety

This project defaults to dry-run mock data. It contains no live trading, private keys, wallet runtime state, signing, swaps, transaction construction, or transaction broadcasting. Aegis is only a pre-trade risk oracle and callable risk-check Service.
