# Aegis Risk Oracle CROO

Aegis Risk Oracle is a callable, chain-agnostic pre-trade risk oracle for CROO Agent Commerce. An agent submits its intended action and current market signals before execution; Aegis returns `BLOCK`, `WAIT`, or `EXECUTE`, along with a deterministic risk score and proof hashes.

It is not a trading bot. Aegis evaluates a proposed action but has no wallet logic, private-key handling, transaction construction, swap endpoint, or broadcast path. Step 1 uses BNB on BSC only as a deterministic demo fixture; the request and oracle boundaries are designed for future provider coverage across BSC, Ethereum, Base, Arbitrum, Polygon, and other chains.

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

Example request:

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

The response contains `decision`, `risk_score`, `confidence`, `market_regime`, `safe_to_execute`, `risk_factors`, `reasons`, `suggested_action`, and a `proof` object with request, response, and policy hashes/version data. Each explainable risk factor contains a guard `name`, `severity`, `score_impact`, and deterministic `evidence`.

## Safety

This project defaults to dry-run mock data. It contains no live trading, no private keys, no wallet runtime state, and no transaction broadcasting. An `EXECUTE` response is advice to a separately controlled caller; Aegis itself cannot execute or broadcast anything.
