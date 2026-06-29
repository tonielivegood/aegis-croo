# CROO Python SDK Contract Verification - Step 6A

Date: 2026-06-29

## Scope

Step 6A verified the official CROO Python SDK contract enough to plan Step 6B safely.

This note is documentation only. It does not install `croo-sdk`, import it in application code, call the CROO/CAP API, use credentials, create orders, pay orders, upload files, deliver results, settle, clear, or execute any live CAP action.

## Sources Checked

- PyPI project: `croo-sdk` version `0.2.1`
- Official package source distribution from PyPI: `croo_sdk-0.2.1.tar.gz`
- Package repository listed in official package metadata: `https://github.com/CROO-Network/python-sdk`

## Verified Facts

### Package and Import

- Python package name: `croo-sdk`
- Python import package: `croo`
- Exported client: `from croo import AgentClient`
- Exported config type: `from croo import Config`
- Requires Python `>=3.10,<4.0`
- Runtime dependencies declared by package metadata:
  - `httpx>=0.27`
  - `websockets>=13.0`

### AgentClient Constructor

Verified source signature:

```python
def __init__(self, config: Config, sdk_key: str) -> None:
```

`Config` is a dataclass with:

```python
@dataclass
class Config:
    base_url: str
    ws_url: str = ""
    rpc_url: str = ""
```

Constructor behavior verified from source:

- Raises `ValueError("croo: base_url is required")` if `config.base_url` is empty.
- Raises `ValueError("croo: sdk_key is required")` if `sdk_key` is empty.
- Creates an internal async HTTP client using `config.base_url`.
- Stores the SDK key internally.
- Stores `config.ws_url`.
- Uses `config.rpc_url` or defaults to `https://mainnet.base.org`.

### Sync or Async Behavior

- `AgentClient(...)` construction is synchronous.
- Runtime methods are asynchronous and must be awaited.
- `close`, order methods, delivery methods, object storage methods, and `connect_websocket` are all `async def`.

### API Key and Auth Behavior

Verified from README and source:

- SDK auth uses an SDK key from the CROO Dashboard.
- Documented environment variable: `CROO_SDK_KEY`
- Documented example format: `croo_sk_...`
- HTTP auth header name: `X-SDK-Key`
- Source sets the header value directly to the provided SDK key.
- No bearer prefix is documented or added by the SDK source.

Step 6B must treat `CROO_SDK_KEY` as secret and must never print, serialize, log, commit, or expose its value or fragments.

### Base API URL Behavior

Verified from README and source:

- Documented environment variable: `CROO_API_URL`
- Documented example/default API base URL: `https://api.croo.network`
- `Config.base_url` is required.
- Internal HTTP client appends `/backend/v1` to `Config.base_url`.
- Base URL override is done by passing `Config(base_url=...)`.

### WebSocket URL Behavior

Verified from README and source:

- Documented environment variable: `CROO_WS_URL`
- Documented example WebSocket URL: `wss://api.croo.network/ws`
- `Config.ws_url` defaults to an empty string.
- `ws_url` is required only when calling `connect_websocket`.
- `connect_websocket` raises `ValueError("croo: ws_url is required for WebSocket connection")` when `ws_url` is empty.
- WebSocket auth uses the SDK key as a `key` query parameter when connecting.

Step 6B provider readiness should not require WebSocket connection unless official docs later identify a read-only readiness check that specifically needs it.

### Safe Read-Only Methods Available

Verified `AgentClient` methods that use HTTP `GET` and are read-only by SDK source:

- `await get_negotiation(negotiation_id)`
- `await list_negotiations(opts=None)`
- `await get_order(order_id)`
- `await list_orders(opts=None)`
- `await get_delivery(order_id)`

Potentially useful Step 6B read-only auth check:

- `await list_orders(ListOptions(role="provider", agent_id=CROO_PROVIDER_AGENT_ID, page=1, page_size=1))`

Important limitation:

- The SDK has no documented `auth_status`, `health`, `me`, `get_agent`, `get_provider`, `get_service`, or `get_service_by_id` method.
- The SDK has no direct service/provider lookup method in the verified `AgentClient` API.
- `list_orders` can prove that the SDK key can authenticate if the request succeeds, but it cannot prove service registration by itself, especially when no orders exist.

### Error and Exception Behavior

Verified exported error classes and helpers:

- `APIError`
- `InsufficientBalanceError`
- `is_not_found`
- `is_unauthorized`
- `is_invalid_params`
- `is_invalid_status`
- `is_forbidden`
- `is_insufficient_balance`

Verified `APIError` fields:

```python
self.http_status = http_status
self.code = code
self.reason = reason
```

The exception message may include backend-provided `message` text.

Safe Step 6B status exposure:

- Safe to expose coarse categories such as `unauthorized`, `not_found`, `forbidden`, `invalid_params`, `invalid_status`, `sdk_missing`, `sdk_import_error`, `client_init_error`, `read_only_check_failed`, and `provider_or_service_unverified`.
- Safe to expose whether a required environment variable is `present` or `missing`.
- Avoid exposing raw exception messages by default.
- Avoid exposing URLs containing credentials, SDK key values, request headers, response bodies, or backend messages that might echo sensitive input.

## Unknowns / Needs Human Confirmation

- No official SDK method was found for direct provider identity lookup.
- No official SDK method was found for direct service ID lookup.
- No official SDK method was found for a read-only auth/status endpoint.
- No official SDK method was found to verify that `CROO_SERVICE_ID` belongs to `CROO_PROVIDER_AGENT_ID` without using existing order data or a Dashboard/manual confirmation.
- It is unknown whether the CROO Dashboard or a separate official API endpoint exposes a safe read-only service/provider verification path outside `AgentClient`.
- It is unknown whether an empty successful `list_orders` response is intended by CROO to prove SDK-key validity for readiness purposes. It proves only that the call authenticated and returned, not that a target service is registered.

Because of these unknowns, Step 6B must not mark `real_cap_ready=true` using SDK v0.2.1 alone unless provider and service identity are verified through an official safe read-only method or manual Dashboard evidence is explicitly accepted as the readiness source.

## Forbidden Methods for Step 6B Readiness

Step 6B readiness must not call:

- `negotiate_order`
- `accept_negotiation`
- `accept_negotiation_with_fund_address`
- `reject_negotiation`
- `pay_order`
- `deliver_order`
- `reject_order`
- `upload_file`
- `get_download_url`
- Any method that creates, accepts, rejects, pays, settles, clears, uploads, delivers, or otherwise mutates a real CAP order or related payment/file/delivery state.

Step 6B must not add wallet, private key, signing, swap, transaction construction, broadcast, escrow, settlement, clear, or live trading logic.

## Proposed Safe Readiness Algorithm for Step 6B

1. Load environment configuration without printing values:
   - `CAP_MODE`
   - `CROO_API_URL`
   - `CROO_WS_URL`
   - `CROO_SDK_KEY`
   - `CROO_SERVICE_ID`
   - `CROO_PROVIDER_AGENT_ID`
2. If `CAP_MODE != "real"`, keep mock-mode status and do not import the SDK.
3. If any required real-mode config is missing, return `real_cap_ready=false` with missing variable names only.
4. Lazily import `AgentClient`, `Config`, `ListOptions`, `APIError`, and documented error helper functions.
5. If import fails, return `real_cap_ready=false` with `sdk_import_status="missing_or_failed"` and no raw exception message.
6. Initialize `AgentClient(Config(base_url=CROO_API_URL, ws_url=CROO_WS_URL), CROO_SDK_KEY)`.
7. If initialization fails, return `real_cap_ready=false` with `adapter_status="REAL_CAP_CLIENT_INIT_FAILED"` and no raw secret-bearing details.
8. Run only a safe read-only auth check, preferably:

   ```python
   await client.list_orders(ListOptions(
       role="provider",
       agent_id=CROO_PROVIDER_AGENT_ID,
       page=1,
       page_size=1,
   ))
   ```

9. Classify documented errors without exposing secrets:
   - Unauthorized helpers -> auth failure.
   - Forbidden helpers -> forbidden.
   - Invalid params helpers -> configuration or SDK contract mismatch.
   - Other `APIError` -> read-only check failed, exposing only safe category fields.
10. Close the client with `await client.close()` if it was created.
11. Provider/service identity verification:
   - If a future official safe read-only method exists, use it to verify exact `CROO_PROVIDER_AGENT_ID` and `CROO_SERVICE_ID`.
   - If only SDK v0.2.1 methods are available, keep `real_cap_ready=false` with provider/service identity unverified.
12. Set `real_cap_ready=true` only if all of the following are true:
   - `CAP_MODE=real`
   - `CROO_SDK_KEY` is present but never printed
   - `CROO_SERVICE_ID` is present
   - SDK import succeeds
   - `AgentClient` initializes successfully
   - Safe read-only auth/status check succeeds
   - Provider identity is verified
   - Service identity is verified
   - No forbidden method was called

## Conditions for `real_cap_ready=false`

Return false when any of these occur:

- Missing real-mode credentials or config.
- SDK package missing.
- SDK import error.
- `AgentClient` initialization error.
- Auth failure.
- Read-only status/auth check failure.
- Service ID mismatch.
- Provider identity mismatch.
- Service/provider identity cannot be verified from official safe read-only methods.
- Any unsafe method would be required to prove readiness.

## Tests Needed for Step 6B

All tests must be mock-only and require no real credentials:

- Mock mode does not import `croo`.
- Missing credentials return `real_cap_ready=false` with variable names only.
- Missing SDK returns `real_cap_ready=false` gracefully.
- SDK import error returns a sanitized status.
- Fake `AgentClient` constructor failure returns a sanitized status.
- Fake `list_orders` unauthorized error returns auth failure without leaking the SDK key.
- Fake successful `list_orders` alone does not mark ready unless provider and service identity verification are also faked as successful through a safe read-only verifier.
- Fake full readiness can mark `real_cap_ready=true` only if:
  - SDK import succeeds
  - client initializes
  - safe read-only check succeeds
  - provider identity matches
  - service ID matches
  - no forbidden methods are called
- Fake SDK records calls and tests assert forbidden methods are never called:
  - `negotiate_order`
  - `accept_negotiation`
  - `accept_negotiation_with_fund_address`
  - `reject_negotiation`
  - `pay_order`
  - `deliver_order`
  - `reject_order`
  - `upload_file`
  - `get_download_url`
- `/cap/status` serialization never includes secret values, raw auth headers, or raw exception messages.
- Existing `/cap/order` real-mode tests continue to return no fake success until a later approved step explicitly implements real order behavior.

## Step 6B Boundary

Step 6B may implement provider readiness status only. It must not implement real CAP order creation, payment, escrow, settlement, clearing, upload, delivery, wallet, signing, transaction construction, broadcast, swaps, or live trading.
