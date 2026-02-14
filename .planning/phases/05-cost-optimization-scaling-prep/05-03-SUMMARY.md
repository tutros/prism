---
phase: 05-cost-optimization-scaling-prep
plan: 03
subsystem: infra, frontend
tags: [monitoring, spending-cap, cache-indicator, deduplication, force-refresh]

# Dependency graph
requires:
  - plan: 05-01
    provides: usage_tracker.get_usage_stats(), spending_guard.check_spending_cap/get_daily_spend
  - plan: 05-02
    provides: tavily_service TTLCache, OptionResearch.cached_at, force_refresh parameter
provides:
  - GET /api/monitoring endpoint with usage stats, daily spend, cache stats
  - POST /api/compare returns 429 when daily cap exceeded
  - POST /api/compare deduplication for identical inputs within 24h
  - Frontend cache age banner with "Refresh with latest data" button
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Comparison deduplication via SHA-256 hash of lowercased inputs"
    - "Dedup stamps tavily_cached_at on existing result for cache banner visibility"
    - "force_refresh query param flows through POST /compare -> orchestrator -> Tavily"
    - "spending_guard loads today costs from disk on startup for restart resilience"

key-files:
  created:
    - backend/app/routers/monitoring.py
  modified:
    - backend/app/main.py
    - backend/app/routers/comparison.py
    - backend/app/services/tavily_service.py
    - backend/app/services/spending_guard.py
    - frontend/src/features/comparison/types.ts
    - frontend/src/features/results/ResultsDisplay.tsx
    - frontend/src/App.tsx

key-decisions:
  - "Dedup returns existing comparison_id with 200 (not 202) - frontend handles both"
  - "Cache age banner uses amber styling consistent with existing banner patterns"
  - "Refresh button creates new comparison with force_refresh=true rather than mutating existing"
  - "Prompt caching annotation is correct but system prompt (~150 tokens) is below Anthropic minimum (~1024 tokens) - silently inactive"

patterns-established:
  - "queryClient.invalidateQueries on handleNewComparison to handle dedup returning same id"

# Metrics
duration: ~15min (across sessions, including 5 bug fixes during verification)
completed: 2026-02-13
---

# Phase 5 Plan 03: Monitoring Endpoint + Frontend Cache Indicator Summary

**Developer monitoring dashboard, spending cap enforcement, comparison dedup, and frontend cache age indicator with refresh capability**

## Performance

- **Duration:** ~15 min (across two sessions)
- **Completed:** 2026-02-13
- **Tasks:** 2 auto + 1 human-verify checkpoint
- **Files modified:** 8 (1 created, 7 modified)
- **Bug fixes during verification:** 5

## Accomplishments

- Created GET /api/monitoring endpoint returning token usage breakdown, daily spend vs cap, and Tavily cache stats
- Wired check_spending_cap() as pre-flight check in POST /api/compare (returns 429 when exceeded)
- Added comparison deduplication: identical option_a + option_b + intent within 24h returns existing result
- Added force_refresh query param flowing through to Tavily search
- Created frontend cache age banner with "Refresh with latest data" button
- Added get_cache_stats() to tavily_service.py

## Bug Fixes During Verification

1. `69cac89` — storage.py: usage_metrics.json in data/ crashed list_results (ValidationError on non-ComparisonResult files)
2. `4938c6a` — comparison.py: dedup never set tavily_cached_at, so cache banner never appeared
3. `4f96485` — ResultsDisplay.tsx: window.location.reload() cleared React state; switched to onNewComparison callback
4. `bcc64f0` — App.tsx: dedup returning same comparison_id didn't trigger TanStack Query refetch; added invalidateQueries
5. `c93d5b7` — spending_guard.py: daily cost started at $0 on restart; now loads today's accumulated costs from disk

## Task Commits

1. **Task 1: Monitoring endpoint + spending cap + dedup** - `0d5699b` (feat)
2. **Task 2: Frontend cache age indicator + refresh button** - `59dd3bf` (feat)

## Known Limitations

- **Prompt caching inactive:** The `cache_control: {"type": "ephemeral"}` annotation on the system prompt is architecturally correct, but the system prompt (~150 tokens) is below Anthropic's minimum (~1024 tokens) for caching to activate. cache_creation_tokens and cache_read_tokens remain 0. Would activate with larger system prompts at scale.

## Deviations from Plan

- Refresh button uses `onNewComparison` callback (React state navigation) instead of `window.location.reload()` — discovered during verification that reload clears React state
- Added queryClient.invalidateQueries for comparison data on dedup — discovered stale TanStack Query cache prevented banner display

## Issues Encountered

All 5 bugs found during human verification were root-caused and fixed. No workarounds or temporary fixes.

---
*Phase: 05-cost-optimization-scaling-prep*
*Completed: 2026-02-13*
