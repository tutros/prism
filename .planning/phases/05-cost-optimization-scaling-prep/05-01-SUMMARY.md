---
phase: 05-cost-optimization-scaling-prep
plan: 01
subsystem: infra
tags: [usage-tracking, cost-monitoring, spending-cap, token-metering, claude-api]

# Dependency graph
requires:
  - phase: 02-ai-integration-async-orchestration
    provides: claude_service, criteria_service, flip_service with Claude API calls
  - phase: 03-interactive-analysis-flip-detection
    provides: criteria_service and flip_service additional call sites
provides:
  - usage_tracker.py with UsageRecord, calculate_cost, record_usage, get_usage_stats
  - spending_guard.py with check_spending_cap, add_cost, get_daily_spend
  - All 4 Claude API call sites instrumented for token/cost tracking
  - Persistent usage_metrics.json for cost visibility across restarts
affects:
  - 05-02 (caching): may read usage stats to measure cache hit savings
  - 05-03 (monitoring dashboard): reads get_usage_stats() and get_daily_spend()

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "threading.Lock for fast in-memory accumulator (not asyncio.Lock)"
    - "Atomic tempfile+fsync+os.replace write pattern (consistent with storage.py)"
    - "Lazy import of add_cost inside record_usage to avoid circular import"
    - "Graceful persistence failure: never fail Claude call because of metrics write error"
    - "Day-boundary reset checked on every add_cost/check_spending_cap call"

key-files:
  created:
    - backend/app/services/usage_tracker.py
    - backend/app/services/spending_guard.py
  modified:
    - backend/app/services/claude_service.py
    - backend/app/services/criteria_service.py
    - backend/app/services/flip_service.py

key-decisions:
  - "PRICE_PER_TOKEN dict keyed by model string for future multi-model support"
  - "getattr with None fallback for cache tokens (API may omit these fields)"
  - "record_usage never raises even on disk failure (try/except around persist)"
  - "DAILY_SPEND_CAP_USD=5.0 default - conservative cap for development"
  - "Path resolved as Path(__file__).parent.parent.parent/data to match server cwd pattern"

patterns-established:
  - "record_usage call placed immediately after response = await client.messages.create()"
  - "Feature name string matches function name: criteria/go_deeper/regenerate_weights/flip_suggestions"

# Metrics
duration: 2min
completed: 2026-02-12
---

# Phase 5 Plan 01: Token Usage Tracking + Daily Spending Cap Summary

**In-memory + persistent token metering for all 4 Claude API call sites, with configurable daily spending cap via DAILY_SPEND_CAP_USD env var**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-02-13T01:19:17Z
- **Completed:** 2026-02-13T01:21:19Z
- **Tasks:** 2
- **Files modified:** 5 (2 created, 3 modified)

## Accomplishments

- Created `usage_tracker.py` with token pricing, cost calculation, atomic persistence to `data/usage_metrics.json`, and aggregated stats by feature
- Created `spending_guard.py` with configurable daily cap (env var), auto day-boundary reset, and ValueError on cap exceeded
- Wired `record_usage()` into all 4 Claude API call sites across 3 service files with zero changes to existing logic

## Task Commits

Each task was committed atomically:

1. **Task 1: Create usage_tracker.py and spending_guard.py** - `84c8dac` (feat)
2. **Task 2: Wire usage tracking into all Claude API call sites** - `b5e43cf` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `backend/app/services/usage_tracker.py` - UsageRecord dataclass, PRICE_PER_TOKEN, calculate_cost(), record_usage(), get_usage_stats(), startup disk restore
- `backend/app/services/spending_guard.py` - _DAILY_CAP_USD from env, check_spending_cap(), add_cost(), get_daily_spend() with day-boundary reset
- `backend/app/services/claude_service.py` - Added import + `record_usage("criteria", ...)` after API call
- `backend/app/services/criteria_service.py` - Added import + `record_usage("go_deeper", ...)` and `record_usage("regenerate_weights", ...)`
- `backend/app/services/flip_service.py` - Added import + `record_usage("flip_suggestions", ...)` after API call

## Decisions Made

- Used `threading.Lock` (not asyncio) for both modules — these are fast in-memory operations, and asyncio locks require an event loop context
- `record_usage` uses a lazy local import of `add_cost` from spending_guard to avoid circular import at module load time
- Persistence failures are silently swallowed so a disk error never kills an active Claude API call
- `getattr(usage, "cache_creation_input_tokens", None) or 0` pattern handles API versions that omit cache fields
- `Path(__file__).parent.parent.parent / "data"` gives absolute path to `backend/data/` regardless of working directory

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

Optional: Set `DAILY_SPEND_CAP_USD` environment variable to override the $5.00 default daily cap.

```bash
export DAILY_SPEND_CAP_USD=10.0  # Increase cap to $10/day
```

## Next Phase Readiness

- `get_usage_stats()` and `get_daily_spend()` ready for Plan 03 monitoring dashboard to consume
- All Claude calls now metered; Plan 02 (prompt caching) can verify cache hit rates via `total_cache_read_tokens`
- `check_spending_cap()` available for Plan 02/03 to wire into comparison submission flow if desired

---
*Phase: 05-cost-optimization-scaling-prep*
*Completed: 2026-02-12*
