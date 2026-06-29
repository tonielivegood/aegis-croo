# Explainable Guard Risk Engine Design

## Goal

Refactor Aegis Risk Oracle's Step 1 deterministic classifier into a modular,
chain-agnostic collection of explainable pre-trade risk guards. The service
continues to return advice only and contains no execution, wallet, key, swap,
provider, or transaction-broadcasting path.

## Scope

Step 2 adds eight guards: volatility, liquidity, volume, exposure, slippage,
gas, unknown token/market, and suspicious pump. CAP, web UI, live providers,
portfolio-check endpoints, and marketplace documentation remain out of scope.
BNB on BSC remains a demo fixture in a replaceable supported-market registry,
not a product-level chain restriction.

## Guard Interface and Risk Factors

`BaseGuard.evaluate(request)` returns one `RiskFactor` or `None`. A triggered
factor contains exactly:

- `name`
- `severity`: `low`, `medium`, `high`, or `critical`
- `score_impact`: a non-negative integer
- `evidence`: a concise deterministic explanation with the observed values

The oracle evaluates all guards in a fixed order, preserves their factors in
that order, and computes `risk_score = min(100, sum(score_impact))`.

## Scoring Policy

| Guard condition | Severity | Impact |
|---|---:|---:|
| volatility >= 7 and < 12 | medium | 35 |
| volatility >= 12 | critical | 70 |
| size/liquidity > 0.01 and <= 0.05 | medium | 35 |
| size/liquidity > 0.05 | high | 70 |
| liquidity missing | medium | 35 |
| buy with volume change < 0 | medium | 35 |
| buy with volume change >= 0 and < 5 | low | 15 |
| exposure exceeds max position | high | 70 |
| slippage > 300 and <= 600 bps | medium | 35 |
| slippage > 600 bps | high | 70 |
| gas high | medium | 35 |
| gas critical | high | 70 |
| unsupported token/market | high | 70 |
| price change > 40 and liquidity < 50,000 | critical | 100 |

Threshold boundaries are exact: values equal to 300 or 600 bps do not enter
the next band; a liquidity ratio equal to 0.01 or 0.05 does not enter the next
band. Missing optional portfolio context never adds risk by itself.

## Missing Data and Confidence

The four important market fields remain price change, volume change,
liquidity, and volatility. If any are absent, the result cannot be EXECUTE.
Missing liquidity produces its guard factor; other missing important fields
are recorded as deterministic missing-data evidence. If accumulated risk is
below WAIT, the oracle raises the effective score to 35. Confidence is `low`
when important market data is incomplete, `medium` for an unsupported market,
and `high` when complete fixture data supports the classification.

Optional slippage, gas, and portfolio context do not count as missing
important market data because their absence means that check was not supplied,
not that core market evidence is complete.

## Decisions and Response

- 0-34: `EXECUTE`
- 35-69: `WAIT`
- 70-100: `BLOCK`

`safe_to_execute` is true only for `EXECUTE`. The response includes decision,
risk score, confidence, market regime, safety flag, ordered risk factors,
human-readable reasons, suggested action, and the existing deterministic proof.
Proof hashing includes the new risk-factor payload.

Market regimes remain stable for acceptance scenarios: `safe_small_buy`,
`volatile_buy`, `missing_data`, `unknown_market`, `high_slippage`,
`suspicious_pump`, and `overexposed_portfolio`; other guarded outcomes use a
generic `elevated_risk` or `uncertain_market` regime.

## Schema Changes

Add `RiskFactor` and `PortfolioContext`. Extend market signals with optional
`slippage_bps` and `gas_level`, and extend the request with optional
`portfolio_context`. Add `risk_factors` to `RiskCheckResponse`. Validation
keeps monetary and bps values non-negative and restricts gas level to the
supported deterministic levels.

## Testing

Unit tests instantiate each guard with real request models and verify its
factor name, severity, impact, and evidence. API tests cover volatile buy,
safe small buy, missing data, unknown market, high slippage, suspicious pump,
and overexposure. The full suite also verifies the response shape, proof, API
health, and absence of regressions.

## Self-Review

- No placeholders or deferred decisions remain.
- Score impacts satisfy all specified decision thresholds and acceptance cases.
- Missing core data cannot default to EXECUTE.
- The design adds no live provider or execution capability.
- All changes are confined to Step 2 guards, risk schema/oracle, tests, and a
  minimal README response-field update if required.
