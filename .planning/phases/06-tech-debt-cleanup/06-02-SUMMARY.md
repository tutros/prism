---
phase: 06-tech-debt-cleanup
plan: 02
subsystem: ui
tags: [fetch, error-handling, fastapi, http, typescript]

# Dependency graph
requires:
  - phase: 01-foundation-core-trust
    provides: apiPost helper in frontend/src/lib/api.ts
  - phase: 05-cost-optimization-scaling-prep
    provides: spending_guard raising HTTPException(429) with detail message
provides:
  - apiPost that surfaces FastAPI HTTPException detail messages to the user
affects: [any future plan that calls apiPost and wants meaningful error messages]

# Tech tracking
tech-stack:
  added: []
  patterns: [parse error response body before throwing; surface body.detail from FastAPI HTTPException]

key-files:
  created: []
  modified:
    - frontend/src/lib/api.ts

key-decisions:
  - "Inline try/catch in error branch — no custom error classes, no middleware layer, no changes to apiGet"
  - "Fall back to 'API error: {status}' if body is non-JSON or detail field is absent"

patterns-established:
  - "Error body parsing pattern: try res.json() in error branch, read body.detail, catch silently"

# Metrics
duration: 3min
completed: 2026-02-14
---

# Phase 6 Plan 02: Surface FastAPI Error Detail in apiPost Summary

**apiPost now parses error response body and surfaces FastAPI HTTPException detail so "Daily spending cap of $X.XX reached" replaces "API error: 429"**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-02-14T00:00:00Z
- **Completed:** 2026-02-14T00:03:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Replaced single-line status-code throw in apiPost with a body-parsing error branch
- FastAPI detail messages (e.g., spending cap, validation errors) now reach the user as readable text
- apiGet left completely untouched per plan instructions

## Task Commits

Each task was committed atomically:

1. **Task 1: Parse error response body in apiPost** - `812b8e6` (fix)

**Plan metadata:** (docs commit follows this summary)

## Files Created/Modified

- `frontend/src/lib/api.ts` - apiPost error branch now reads res.json() and surfaces body.detail; apiGet unchanged

## Decisions Made

- Used inline try/catch rather than a helper or custom error class — keeps the change minimal and the file simple
- Fall back to status-code message if body cannot be parsed as JSON (non-JSON error bodies from proxies, etc.)
- Only apiPost modified — apiGet is separate concern and plan explicitly prohibited touching it

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Error surface fix complete; spending cap UX now works end-to-end
- No blockers for remaining Phase 6 plans

---
*Phase: 06-tech-debt-cleanup*
*Completed: 2026-02-14*
