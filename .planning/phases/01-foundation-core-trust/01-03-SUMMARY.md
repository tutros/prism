---
phase: 01-foundation-core-trust
plan: 03
subsystem: ui
tags: [react, tanstack-query, typescript, tailwind, fetch, polling]

# Dependency graph
requires:
  - phase: 01-foundation-core-trust plan 01
    provides: FastAPI backend with POST /api/compare (202 Accepted) and GET /api/results/{id} endpoints
  - phase: 01-foundation-core-trust plan 02
    provides: Vite + React 19 + TanStack Query v5 frontend scaffold with queryClient singleton
provides:
  - API client helpers (apiGet, apiPost) in src/lib/api.ts
  - TypeScript types mirroring backend Pydantic models
  - Comparison form with controlled inputs and client-side validation
  - useMutation hook for POST /api/compare submission
  - useQuery hook with 1s polling for GET /api/results/{id}
  - Results display: spinner, winner banner, side-by-side options, criteria with scores and source links
  - Wired App.tsx: submit -> poll -> display flow
affects:
  - 01-04 (weight system UI builds on criteria display and types)
  - 01-05 (persistence + polish adds to this flow)
  - All Phase 2+ frontend work

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "useMutation from TanStack Query for POST submissions returning comparison_id"
    - "useQuery with dynamic refetchInterval callback for status-based polling (stops at completed/error)"
    - "import type for type-only imports (required by verbatimModuleSyntax: true)"
    - "Feature-scoped directory structure: src/features/{feature}/ with types, hooks, components"

key-files:
  created:
    - frontend/src/lib/api.ts
    - frontend/src/features/comparison/types.ts
    - frontend/src/features/comparison/useComparison.ts
    - frontend/src/features/comparison/ComparisonForm.tsx
    - frontend/src/features/results/useResults.ts
    - frontend/src/features/results/ResultsDisplay.tsx
  modified:
    - frontend/src/App.tsx

key-decisions:
  - "refetchInterval uses query.state.data to conditionally stop polling -- TanStack Query v5 passes the Query object (not raw data) to the refetchInterval callback"
  - "apiPost/apiGet use res.ok check which covers 202 Accepted from the 202-pattern backend"

patterns-established:
  - "Pattern: Feature directories under src/features/ with co-located types, hooks, and components"
  - "Pattern: API helpers in src/lib/ consumed by feature hooks"
  - "Pattern: Polling hook with self-terminating refetchInterval based on result status"

# Metrics
duration: 4min
completed: 2026-02-04
---

# Phase 01 Plan 03: Comparison Flow Summary

**Submit-poll-display flow wiring ComparisonForm mutation through useResults polling to ResultsDisplay with winner banner and scored criteria**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-04T04:49:16Z
- **Completed:** 2026-02-04T04:53:51Z
- **Tasks:** 3
- **Files created:** 6, modified: 1

## Accomplishments
- Created generic API client (apiPost, apiGet) with error handling and TypeScript types mirroring all backend Pydantic models
- Built ComparisonForm with controlled inputs, HTML required + trim validation, pending-state button label, and error display
- Implemented useResults polling hook that auto-stops when the backend reports completed or error status
- Built ResultsDisplay with processing spinner, error card, winner banner with reasoning, side-by-side option cards, per-criterion score breakdown, and clickable source citations
- Wired App.tsx with the complete submit-poll-display pattern: form onSubmit sets comparisonId, useResults polls, ResultsDisplay renders

## Task Commits

Each task was committed atomically:

1. **Task 1: Create API client and types** - `cf1990a` (feat)
2. **Task 2: Create comparison form and submission hook** - `9a68f84` (feat)
3. **Task 3: Create results polling and display** - `f0bf246` (feat)

## Files Created/Modified
- `frontend/src/lib/api.ts` - Generic apiPost/apiGet helpers with status-aware error handling
- `frontend/src/features/comparison/types.ts` - ComparisonInput, Criterion, ComparisonResult, SubmitResponse interfaces
- `frontend/src/features/comparison/useComparison.ts` - useMutation hook wrapping POST /api/compare
- `frontend/src/features/comparison/ComparisonForm.tsx` - Controlled form: Option A, Option B, Intent textarea; validation; pending/error states
- `frontend/src/features/results/useResults.ts` - useQuery hook with 1s polling that self-terminates on completed/error
- `frontend/src/features/results/ResultsDisplay.tsx` - Spinner, error card, winner banner, option cards, criteria with scores and source links
- `frontend/src/App.tsx` - Root component wiring form submission to polling to results display

## Decisions Made
- `refetchInterval` callback receives the TanStack Query `Query` object, not raw data. Access data via `query.state.data`. This is the v5 API.
- `apiPost` uses `res.ok` check which returns true for 202 Accepted -- no special handling needed for the backend's 202 pattern.
- No CORS proxy configured; frontend points directly at `http://localhost:8000`. This works for local development. Production will need a proxy or CORS headers.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required. Both backend and frontend run locally.

## Next Phase Readiness
- Comparison flow is fully wired and verified end-to-end via curl (submit returns 202, immediate poll shows processing, subsequent poll shows completed with 3 criteria, winner, and reasoning)
- Types file is the single source of truth shared between comparison and results features -- 01-04 weight system can import Criterion directly
- useResults polling hook is ready to feed criteria data to the weight system UI (01-04)
- No blockers or concerns for 01-04 or 01-05

---
*Phase: 01-foundation-core-trust*
*Completed: 2026-02-04*
