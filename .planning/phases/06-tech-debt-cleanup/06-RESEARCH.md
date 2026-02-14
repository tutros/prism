# Phase 6: Tech Debt Cleanup - Research

**Researched:** 2026-02-13
**Domain:** Bug fixes — SSE URL routing, HTTP error body parsing, documentation
**Confidence:** HIGH

## Summary

Phase 6 closes three specific tech debt items identified by the v1.0 milestone audit. All three items have already been precisely diagnosed with exact file locations and fix strategies. This is not exploratory research — the problems and solutions are known. The research task here is to confirm the exact current state of each file and verify no secondary effects exist before planning.

**Item 1 (06-01):** `useProgress.ts:33` creates an EventSource with a relative URL `/api/progress/${id}`, which resolves to the Vite dev server at port 5173, not the FastAPI backend at port 8000. All other API calls in `api.ts` use the hardcoded `http://localhost:8000` base. The fix is to change the single EventSource line to use the absolute URL `http://localhost:8000/api/progress/${comparisonId}`. Adding a Vite proxy is a valid alternative but introduces unnecessary config complexity since the rest of the codebase uses absolute URLs.

**Item 2 (06-02):** `apiPost` in `api.ts` throws `new Error('API error: ${res.status}')` on non-OK responses without reading the response body. The FastAPI backend raises `HTTPException(status_code=429, detail=str(e))` for spending cap violations. FastAPI serializes this as `{"detail": "Daily spending cap of $X.XX reached"}`. The fix is to attempt `res.json()` on error responses and surface the `detail` field as the error message, falling back to the status code if parsing fails.

**Item 3 (06-03):** Phase 3 has three completed SUMMARY.md files and user-approved verification checkpoints but no aggregated VERIFICATION.md. This is documentation-only — no code exists to write or verify. The fix is to synthesize the three SUMMARY.md files and the six requirements they satisfy (RES-04, RES-06, WGT-05, RST-02, RST-03, RST-04) into a formal VERIFICATION.md following the format established by Phases 1, 2, 4, and 5.

**Primary recommendation:** Fix 06-01 with a one-line URL change. Fix 06-02 with a try/catch around response body parsing in the error branch of `apiPost`. Write 06-03 VERIFICATION.md from existing SUMMARY content.

## Standard Stack

No new libraries needed for any of the three fixes.

### Existing Stack (Reused)
| Component | Version | Purpose | Used In |
|-----------|---------|---------|---------|
| EventSource (browser native) | Web API | SSE connection | useProgress.ts |
| fetch (browser native) | Web API | HTTP requests | api.ts |
| FastAPI HTTPException | 0.128+ | Error responses with detail | comparison.py |
| React hooks | 19 | State management | useProgress.ts |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Absolute URL in useProgress.ts | Vite proxy config in vite.config.ts | Proxy config is cleaner in production-minded setups but adds a new abstraction. Since all other calls use absolute URLs already, matching that pattern is simpler and consistent. |

**Installation:**
```bash
# No new packages required
```

## Architecture Patterns

### Fix 06-01: EventSource Absolute URL

**Current code (broken):**
```typescript
// frontend/src/features/progress/useProgress.ts:33
const eventSource = new EventSource(`/api/progress/${comparisonId}`)
```

**Fixed code:**
```typescript
// Use absolute URL consistent with api.ts pattern
const API_BASE = 'http://localhost:8000'
const eventSource = new EventSource(`${API_BASE}/api/progress/${comparisonId}`)
```

**Why this works:** The browser resolves relative URLs against the page's origin. In development, the page is served by Vite at port 5173, so `/api/progress/...` resolves to `http://localhost:5173/api/progress/...`. Vite has no proxy configured, so the request never reaches FastAPI at port 8000. Making the URL absolute bypasses Vite entirely.

**Consistency note:** `api.ts` already defines `const API_BASE = 'http://localhost:8000'` at the top. The fix should import or replicate this constant — or simply inline the same string. Since `useProgress.ts` does not currently import from `api.ts`, the simplest approach is to define a local constant or inline the string directly.

### Fix 06-02: apiPost Error Body Parsing

**Current code (broken):**
```typescript
// frontend/src/lib/api.ts
export async function apiPost<T>(endpoint: string, data: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`)  // Body discarded
  }
  return res.json()
}
```

**FastAPI error response format (verified in comparison.py:56-59):**
```python
raise HTTPException(status_code=429, detail=str(e))
# FastAPI serializes as: {"detail": "Daily spending cap of $X.XX reached"}
```

**Fixed code:**
```typescript
export async function apiPost<T>(endpoint: string, data: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    try {
      const body = await res.json()
      throw new Error(body.detail || `API error: ${res.status}`)
    } catch {
      throw new Error(`API error: ${res.status}`)
    }
  }
  return res.json()
}
```

**Important:** The inner `catch` must re-throw as a fallback error, not swallow the exception. If `res.json()` fails (non-JSON error body), the catch falls back to the status-code message.

**Scope:** Only `apiPost` needs this fix based on the audit. The 429 error only occurs on `POST /api/compare`. `apiGet` errors are not spending-cap related.

### Fix 06-03: Phase 3 VERIFICATION.md Content

**Requirements satisfied by Phase 3 (from audit report):**

| Requirement | Description | Plan |
|-------------|-------------|------|
| RES-04 | Go Deeper for additional criteria | 03-02 |
| RES-06 | Add/edit custom criteria | 03-01 |
| WGT-05 | Regenerate weights | 03-02 |
| RST-02 | What would flip the outcome | 03-03 |
| RST-03 | Flip suggestions realistic/actionable | 03-03 |
| RST-04 | Flip suggestions with sources | 03-03 |

**Truths from the three SUMMARY files that serve as verification evidence:**

From 03-01:
- User can add a custom criterion with name, description, scores, and weight
- User can edit any criterion (name, scores)
- User can delete a criterion
- Custom criteria persist after page refresh

From 03-02:
- User can click "Go Deeper" and see 2-3 additional criteria appear
- Go Deeper uses cached research (no new web search)
- User can click "Regenerate Weights" and see weights update
- Custom criteria weights are also regenerated (not deleted)

From 03-03:
- User sees "What would flip this?" analysis with actionable suggestions
- Flip suggestions include source citations
- User can click on a criterion to edit it inline
- User sees which criteria are most sensitive (impact indicator)

**VERIFICATION.md format to follow:** Match the structure of existing phase verifications (Phases 1, 2, 4, 5). The document should list requirements covered, truths verified, artifacts present, and commits.

### Anti-Patterns to Avoid

- **Catch and swallow errors in apiPost:** The inner catch must still throw, just with fallback message
- **Adding Vite proxy:** Inconsistent with the existing codebase pattern of absolute URLs; adds indirection for no benefit in this project
- **Modifying apiGet:** The 429 only occurs on POST /api/compare; apiGet has no spending-cap scenario
- **Over-engineering the error handling:** One try/catch is sufficient — no need for error type hierarchies

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Error message extraction | Custom error parsing middleware | Simple try/catch on res.json() | Problem is one line, not a system |
| SSE URL abstraction | Shared constants module | Inline constant in useProgress.ts | Only one call site; abstraction adds complexity |

## Common Pitfalls

### Pitfall 1: Double-Consuming Response Body
**What goes wrong:** Calling `res.json()` twice on the same Response object (once in error branch, once in success return) throws "body already used"
**Why it happens:** Response body is a stream — it can only be read once
**How to avoid:** The error branch only calls `res.json()` when `!res.ok`, and the success branch only calls it when `res.ok`. There is no overlap. The fix as written above is safe.
**Warning signs:** Runtime error "body used already" in browser console

### Pitfall 2: Inner Catch Re-throw Bug
**What goes wrong:** Inner catch throws a generic error even when JSON parsing succeeded but `body.detail` was undefined
**Why it happens:** `body.detail || fallback` handles undefined correctly — if `body.detail` is falsy, fallback message is used. No issue.
**How to avoid:** Use the `||` fallback pattern shown in the fix.

### Pitfall 3: EventSource CORS in Production
**What goes wrong:** Hardcoding `http://localhost:8000` works in dev but breaks in production
**Why it happens:** Production serves both from same origin or different host
**How to avoid:** This is a dev-environment fix only. The audit is scoped to dev behavior. If production deployment is added later, a shared config pattern should be introduced. Not in scope for this phase.

## Code Examples

### 06-01: The Exact One-Line Fix

```typescript
// frontend/src/features/progress/useProgress.ts
// Before (line 33):
const eventSource = new EventSource(`/api/progress/${comparisonId}`)

// After:
const eventSource = new EventSource(`http://localhost:8000/api/progress/${comparisonId}`)
```

No other changes needed in useProgress.ts. The rest of the SSE handling (onopen, addEventListener, onerror) is correct.

### 06-02: The Full apiPost Fix

```typescript
// frontend/src/lib/api.ts
const API_BASE = 'http://localhost:8000'

export async function apiPost<T>(endpoint: string, data: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    try {
      const body = await res.json()
      throw new Error(body.detail || `API error: ${res.status}`)
    } catch {
      throw new Error(`API error: ${res.status}`)
    }
  }
  return res.json()
}
```

Note: `apiGet` is unchanged. Only `apiPost` is modified.

### 06-03: VERIFICATION.md Structure Reference

The four existing VERIFICATION.md files (Phases 1, 2, 4, 5) establish the expected format. Phase 3 VERIFICATION.md should follow the same pattern: front-matter with phase/status, sections for requirements satisfied, truths verified, artifacts present, commits, and a final verification checklist. Source material: the three SUMMARY.md files in `.planning/phases/03-interactive-analysis-flip-detection/`.

## State of the Art

| Old Approach | Current Approach | Notes |
|--------------|------------------|-------|
| Relative EventSource URL | Absolute URL to backend | Consistent with all other API calls |
| Discard error body | Parse FastAPI detail field | Standard pattern for FastAPI error surfacing |

## Open Questions

1. **Should apiGet also be updated to surface error bodies?**
   - What we know: The audit only flagged apiPost. apiGet does not encounter spending-cap 429s.
   - What's unclear: Whether there are other error scenarios in apiGet where body would help.
   - Recommendation: Keep apiGet unchanged for now. Minimal scope change.

2. **Should the localhost:8000 URL be extracted to a shared constant?**
   - What we know: api.ts already has `const API_BASE = 'http://localhost:8000'`. useProgress.ts does not import from api.ts.
   - What's unclear: Whether future plans would benefit from a shared config.
   - Recommendation: Inline the string in useProgress.ts to match the audit's prescribed fix. One constant in one file is not a problem worth solving.

## Sources

### Primary (HIGH confidence)
- Direct file read: `frontend/src/features/progress/useProgress.ts` — confirmed exact URL on line 33
- Direct file read: `frontend/src/lib/api.ts` — confirmed apiPost discards error body
- Direct file read: `frontend/vite.config.ts` — confirmed no proxy configured
- Direct file read: `backend/app/routers/comparison.py:56-59` — confirmed HTTPException(429, detail=str(e)) format
- Direct file read: `.planning/v1.0-MILESTONE-AUDIT.md` — confirmed all three tech debt items
- Direct file read: Phase 3 SUMMARY files (03-01, 03-02, 03-03) — confirmed all truths and commits for VERIFICATION.md

### Secondary (MEDIUM confidence)
- FastAPI HTTPException documentation pattern: detail field serialized as `{"detail": "..."}` — consistent with observed code

## Metadata

**Confidence breakdown:**
- 06-01 SSE URL fix: HIGH — exact line identified, fix is one character change
- 06-02 error body fix: HIGH — exact pattern identified, FastAPI response format confirmed in source
- 06-03 VERIFICATION.md: HIGH — all source material exists in SUMMARY files

**Research date:** 2026-02-13
**Valid until:** 2026-03-13 (stable — all findings from direct source code reads, not external dependencies)
