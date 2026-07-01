# Step 8-A Aegis Web Console Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Serve a production-quality, API-backed Aegis Web Console at `/` without changing existing API behavior or CAP safety boundaries.

**Architecture:** Mount a dedicated vanilla static asset directory from the existing FastAPI application and return its HTML shell from `/`. Browser JavaScript calls only the existing same-origin local/mock endpoints and renders all response data as text.

**Tech Stack:** FastAPI, Starlette `StaticFiles`/`FileResponse`, semantic HTML, vanilla CSS, vanilla JavaScript, pytest/TestClient.

## Global Constraints

- Keep all existing API route paths and behavior unchanged.
- Keep `CAP_MODE=mock` by default and `real_cap_ready=false`.
- Do not add wallet, key, signing, swap, transaction, broadcast, or live-trading behavior.
- Do not add external scripts, analytics, real CROO/CAP calls, listeners, probes, negotiations, or paid orders.
- Do not commit until focused tests, full pytest, diff checks, and forbidden-capability scans pass.

---

### Task 1: Console route and static contract

**Files:**
- Modify: `apps/api/main.py`
- Create: `apps/web/index.html`
- Create: `apps/web/static/styles.css`
- Create: `apps/web/static/app.js`
- Create: `tests/test_web_console.py`

**Interfaces:**
- Consumes: existing FastAPI `app` and API routers.
- Produces: `GET /` HTML and `/static/styles.css`, `/static/app.js` assets.

- [ ] **Step 1: Write failing route/static tests**

```python
def test_root_serves_aegis_web_console() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Aegis Risk Oracle" in response.text

def test_console_static_assets_are_served() -> None:
    assert client.get("/static/styles.css").status_code == 200
    assert client.get("/static/app.js").status_code == 200
```

- [ ] **Step 2: Run tests and verify 404 failures**

Run: `python -m pytest tests/test_web_console.py -q`
Expected: FAIL because `/` and `/static` do not exist.

- [ ] **Step 3: Add the static mount and root response**

```python
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

WEB_ROOT = Path(__file__).resolve().parents[1] / "web"
app.mount("/static", StaticFiles(directory=WEB_ROOT / "static"), name="static")

@app.get("/", include_in_schema=False)
def web_console() -> FileResponse:
    return FileResponse(WEB_ROOT / "index.html")
```

- [ ] **Step 4: Add minimal semantic HTML and empty asset files, then pass route tests**

Run: `python -m pytest tests/test_web_console.py -q`
Expected: PASS.

### Task 2: Product-grade visual shell and required claims

**Files:**
- Modify: `apps/web/index.html`
- Modify: `apps/web/static/styles.css`
- Modify: `tests/test_web_console.py`

**Interfaces:**
- Consumes: `/static/styles.css` and stable section IDs.
- Produces: responsive hero, posture, risk, A2A, order/proof, readiness, and developer sections.

- [ ] **Step 1: Add failing content and safety-copy assertions**

```python
required = [
    "Other agents can hire Aegis before they execute.",
    "Aegis returns BLOCK, WAIT, or EXECUTE with proof.",
    "CAP-ready gated runtime; real payment, delivery, settlement, and commercial readiness are not claimed yet.",
    "/risk-check", "/a2a/mock-order", "/orders", "/proof/", "/cap/status",
]
assert all(value in response.text for value in required)
```

- [ ] **Step 2: Run focused tests and verify missing-copy failures**

Run: `python -m pytest tests/test_web_console.py -q`
Expected: FAIL on the required product claims.

- [ ] **Step 3: Implement semantic sections and responsive CSS**

Use accessible landmarks, explicit labels, visible focus styles, status badges,
responsive grids, monospace JSON/code surfaces, loading states, and no remote
assets. Include the exact honest readiness claim and simulation-only copy.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_web_console.py -q`
Expected: PASS.

### Task 3: Safe local API interactions

**Files:**
- Modify: `apps/web/index.html`
- Modify: `apps/web/static/app.js`
- Modify: `tests/test_web_console.py`

**Interfaces:**
- Consumes: `/health`, `/cap/status`, `/risk-check`, `/a2a/mock-order`, `/orders`, `/orders/{order_id}`, `/proof/{proof_id}`.
- Produces: live posture, risk result, mock A2A result, local order/proof result, copy helpers, and bounded errors.

- [ ] **Step 1: Add failing static safety assertions**

```python
script = client.get("/static/app.js").text
assert "fetch(\"/health\"" in script
assert "fetch(\"/risk-check\"" in script
assert "innerHTML" not in script
assert "localStorage" not in script
```

- [ ] **Step 2: Run focused tests and verify failures**

Run: `python -m pytest tests/test_web_console.py -q`
Expected: FAIL because API interactions are not implemented.

- [ ] **Step 3: Implement safe fetch/render helpers**

```javascript
async function apiRequest(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`);
  return body;
}

function setText(node, value) {
  node.textContent = value == null ? "Not reported" : String(value);
}
```

Wire controls to parsed textarea JSON, relative endpoints, disabled/loading
states, and text-only response renderers. Retain order/proof IDs only in memory.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_web_console.py -q`
Expected: PASS.

### Task 4: Regression and safety verification

**Files:**
- Modify if necessary: `tests/test_web_console.py`
- Modify if necessary: `README.md`

**Interfaces:**
- Consumes: complete console and existing API suite.
- Produces: verified Step 8-A worktree ready for review, not yet committed.

- [ ] **Step 1: Verify focused console and existing route tests**

Run: `python -m pytest tests/test_web_console.py tests/test_health.py tests/test_risk_check.py tests/test_a2a_mock_order.py tests/test_orders.py tests/test_cap_adapter.py -q`
Expected: all pass.

- [ ] **Step 2: Run the full suite**

Run: `python -m pytest -q`
Expected: all pass with only the existing Starlette/httpx warning.

- [ ] **Step 3: Run whitespace and forbidden-capability scans**

Run: `git diff --check`
Expected: exit `0`.

Scan production changes for forbidden wallet/key/signing/swap/transaction/
broadcast/trading paths, CAP mutation calls, generic lifecycle calls,
provider-example references, listener auto-start, and secret access. Expected:
all categories `0`.

- [ ] **Step 4: Verify safe status defaults and final Git scope**

Run the existing `/cap/status` default-mode test and confirm the working tree
contains only Step 8-A design, plan, console, route, test, and optional README
files. Do not commit until all checks pass.
