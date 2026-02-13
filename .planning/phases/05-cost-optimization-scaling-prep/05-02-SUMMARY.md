---
phase: 05-cost-optimization-scaling-prep
plan: 02
subsystem: api
tags: [cachetools, tavily, caching, ttlcache, cost-optimization, python]

# Dependency graph
requires:
  - phase: 02-ai-integration-async-orchestration
    provides: tavily_service.py with search_option/search_both_options, OptionResearch dataclass
  - phase: 04-source-quality-confidence-signals
    provides: ComparisonResult with source_metadata field
provides:
  - In-memory TTLCache for Tavily results (200 entries, 24h TTL)
  - OptionResearch.cached_at field carrying cache timestamp through pipeline
  - ComparisonResult.tavily_cached_at field indicating cached Tavily data
  - force_refresh parameter flowing from orchestrator through Tavily service
affects:
  - 05-cost-optimization-scaling-prep (plan 03 - comparison deduplication at router level)

# Tech tracking
tech-stack:
  added: [cachetools>=5.5.0]
  patterns:
    - TTLCache with asyncio.Lock for thread-safe async access
    - Cache key = full query string (lowercased/stripped) to avoid option name collisions
    - cached_at ISO timestamp carried from cache through dataclass to Pydantic model

key-files:
  created: []
  modified:
    - backend/requirements.txt
    - backend/app/services/tavily_service.py
    - backend/app/models.py
    - backend/app/services/orchestrator.py

key-decisions:
  - "Cache key is the full query string (including suffix), not just option name - prevents cross-option collisions"
  - "maxsize=200 accommodates ~100 unique option pairs before eviction"
  - "ttl=86400 (24h) balances freshness vs API cost savings"
  - "force_refresh stores result back to cache after fresh fetch - no cache poisoning"
  - "tavily_cached_at picks first non-None of research_a.cached_at or research_b.cached_at"

patterns-established:
  - "Cache lock pattern: async with _CACHE_LOCK for both reads and writes"
  - "Cache miss returns OptionResearch with cached_at=None; hit returns with cached_at=ISO timestamp"

# Metrics
duration: 2min
completed: 2026-02-13
---

# Phase 5 Plan 02: Tavily Result Caching Summary

**In-memory TTLCache (cachetools, 200 entries, 24h) eliminates redundant Tavily API calls for identical option searches, with cache timestamp propagation to ComparisonResult.tavily_cached_at**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-02-13T01:20:00Z
- **Completed:** 2026-02-13T01:22:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added cachetools TTLCache to tavily_service.py with 200-entry max and 86400s (24h) TTL
- Cache check before every Tavily API call; force_refresh=True bypasses cache but still stores result
- OptionResearch.cached_at carries ISO timestamp when result came from cache
- ComparisonResult.tavily_cached_at exposed so callers/UI can detect cached responses
- force_refresh parameter flows: generate_comparison -> search_both_options -> search_option

## Task Commits

Each task was committed atomically:

1. **Task 1: Add cachetools dependency and Tavily result cache** - `c991e70` (feat)
2. **Task 2: Add tavily_cached_at to ComparisonResult and wire orchestrator** - `60da657` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `backend/requirements.txt` - Added cachetools>=5.5.0
- `backend/app/services/tavily_service.py` - TTLCache, _CACHE_LOCK, cached_at on OptionResearch, cache logic in search_option, force_refresh param
- `backend/app/models.py` - tavily_cached_at: str | None = None on ComparisonResult
- `backend/app/services/orchestrator.py` - force_refresh param, cache timestamp determination, tavily_cached_at in result

## Decisions Made
- Cache key is full query string (lowercased/stripped), not just option name. This prevents collisions if two options happen to produce the same normalized name but different queries.
- `maxsize=200` chosen to handle ~100 unique option pairs (2 searches per pair) before LRU eviction.
- `force_refresh=True` still stores fresh result in cache so subsequent calls benefit.
- `tavily_cached_at` is the first non-None of `research_a.cached_at or research_b.cached_at` - partial cache hits are surfaced.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Tavily caching complete; Plan 03 (comparison deduplication at router level) can proceed
- force_refresh parameter is in place for router-level deduplication to pass through
- No blockers

---
*Phase: 05-cost-optimization-scaling-prep*
*Completed: 2026-02-13*
