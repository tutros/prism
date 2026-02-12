---
phase: 04-source-quality-confidence-signals
plan: 03
subsystem: ui
tags: [react, typescript, tanstack-query, tailwind, optimistic-update, source-quality]

# Dependency graph
requires:
  - phase: 04-source-quality-confidence-signals/04-01
    provides: SourceMetadata model, confidence field on Criterion, source_metadata on ComparisonResult
  - phase: 04-source-quality-confidence-signals/04-02
    provides: PATCH /api/comparisons/{id}/sources/flag endpoint, SourceMetadata/SourceQuality types in frontend
provides:
  - SourceLink component with color-coded quality badge, domain name, flag toggle button, last_verified tooltip
  - Confidence badge (High/Medium/Low) on AI-generated criteria in CriteriaEditor
  - Optimistic flag toggle mutation with TanStack Query rollback on error
  - Comma-separated source links per criterion (domain names, not numeric refs)
affects: [05-cost-optimization-scaling-prep]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Optimistic update pattern: cancelQueries -> setQueryData -> onError rollback -> onSettled invalidate"
    - "Domain name extraction: new URL(url).hostname.replace('www.', '') with try/catch fallback"
    - "Quality badge map: Record<string, { label, classes }> for O(1) lookup with unknown tier fallback"

key-files:
  created:
    - frontend/src/features/criteria/SourceLink.tsx
  modified:
    - frontend/src/features/criteria/CriteriaEditor.tsx
    - frontend/src/features/results/ResultsDisplay.tsx

key-decisions:
  - "Comma-separated source display: 'Sources: domain1.com, domain2.gov' (not numbered refs)"
  - "Quality badge hidden for 'unknown' tier to reduce visual noise"
  - "Confidence badge shown only for AI-origin criteria (origin === 'ai'), not user-added"
  - "Optimistic flag toggle uses URL as map key (unique per criterion)"
  - "Flag icon uses Unicode U+2691 (solid flag) - no icon library dependency"

patterns-established:
  - "SourceLink: self-contained component handles own mutation + optimistic update"
  - "Backward compatibility: result.source_metadata ?? {} for pre-Phase-4 comparisons"

# Metrics
duration: 15min
completed: 2026-02-11
---

# Phase 4 Plan 03: Source Quality UI Summary

**Source quality badges, confidence signals, and flag-toggle UI wired to SourceMetadata backend with optimistic TanStack Query mutations**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-02-11T00:00:00Z
- **Completed:** 2026-02-11T00:15:00Z
- **Tasks:** 2 (+ 1 checkpoint approved)
- **Files modified:** 3

## Accomplishments

- Created SourceLink component displaying color-coded quality tier badge (Peer/Gov/Ind/News/Blog), domain name, flag button, and last_verified tooltip
- Added confidence badge to CriteriaEditor for AI-generated criteria showing High/Medium/Low confidence levels
- Replaced numeric source references with readable domain names in comma-separated format
- Optimistic flag toggle: UI updates immediately, rolls back on API error, invalidates cache on settle
- Backward-compatible: pre-Phase-4 comparisons load without errors (source_metadata defaults to {})

## Task Commits

Each task was committed atomically:

1. **Task 1: Create SourceLink component** - `d0e84cb` (feat)
2. **Task 2: Update CriteriaEditor + ResultsDisplay** - `f585808` (feat)

## Files Created/Modified

- `frontend/src/features/criteria/SourceLink.tsx` - New component: quality badge, domain name, flag toggle, tooltip
- `frontend/src/features/criteria/CriteriaEditor.tsx` - Added confidence badge, replaced source display with SourceLink, added sourceMetadata prop
- `frontend/src/features/results/ResultsDisplay.tsx` - Passes sourceMetadata={result.source_metadata ?? {}} to CriteriaEditor

## Decisions Made

- Quality badge hidden for "unknown" tier to avoid cluttering sources with no metadata
- Confidence badge only on AI-origin criteria — user-added criteria skip confidence display
- Comma-separated sources per locked project decision (not numbered [1][2][3])
- Flag icon as Unicode U+2691 avoids adding an icon library dependency

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 4 complete: all source quality and confidence signal requirements satisfied (SRC-01 through SRC-05)
- Phase 5 (Cost Optimization + Scaling Prep) can proceed: search caching, prompt caching, cost tracking are independent of UI changes made here
- No blockers

---
*Phase: 04-source-quality-confidence-signals*
*Completed: 2026-02-11*
