---
phase: 02-ai-integration-async-orchestration
plan: 01
subsystem: api
tags: [anthropic, tavily, asyncio, web-search, ai-integration]

# Dependency graph
requires:
  - phase: 01-foundation-core-trust
    provides: Backend FastAPI app structure, services directory pattern
provides:
  - AI library dependencies (anthropic, tavily-python, sse-starlette)
  - API client configuration with singleton pattern
  - Tavily web search service with parallel execution
  - Search query targeting hidden costs and externalities
affects: [02-02-criteria-discovery, 02-03-llm-orchestration, source-quality]

# Tech tracking
tech-stack:
  added: [anthropic>=0.40.0, tavily-python>=0.7.21, sse-starlette>=2.2.1]
  patterns: [lru_cache for singleton clients, asyncio.gather for parallelism, dataclasses for structured returns]

key-files:
  created:
    - backend/app/services/__init__.py
    - backend/app/services/config.py
    - backend/app/services/tavily_service.py
  modified:
    - backend/requirements.txt

key-decisions:
  - "Use lru_cache for singleton-style API client reuse"
  - "Query design targets hidden costs, subsidies, externalities, supply chain"
  - "asyncio.gather with return_exceptions=True for graceful partial failures"
  - "search_depth=basic for balanced speed/quality"

patterns-established:
  - "API clients cached via lru_cache in config.py"
  - "Service modules import from config for client access"
  - "Dataclasses for structured async function returns"
  - "Parallel async execution via asyncio.gather with exception handling"

# Metrics
duration: 2min
completed: 2026-02-07
---

# Phase 2 Plan 01: AI Dependencies and Tavily Service Summary

**Parallel web search foundation with anthropic, tavily-python, and async orchestration patterns**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-07T23:06:54Z
- **Completed:** 2026-02-07T23:09:07Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- Added AI library dependencies for Claude API and Tavily web search
- Created services/ package with singleton API client configuration
- Implemented parallel web search service targeting hidden costs and externalities
- Established async patterns using asyncio.gather for 50% latency reduction

## Task Commits

Each task was committed atomically:

1. **Task 1: Add AI dependencies** - `ff3fead` (chore)
2. **Task 2: Create services config** - `5f1192c` (feat)
3. **Task 3: Create Tavily service** - `d48a690` (feat)

## Files Created/Modified
- `backend/requirements.txt` - Added anthropic>=0.40.0, tavily-python>=0.7.21, sse-starlette>=2.2.1
- `backend/app/services/__init__.py` - Services package marker
- `backend/app/services/config.py` - get_anthropic_client() and get_tavily_client() with lru_cache
- `backend/app/services/tavily_service.py` - search_option() and search_both_options() with parallel execution

## Decisions Made

**Use lru_cache for API client singletons**
- Rationale: Reuse client instances across requests without global state
- Pattern: Each client getter decorated with @lru_cache()
- Benefit: Thread-safe, lazy initialization, automatic caching

**Query design targets non-obvious criteria**
- Query template: "{option} hidden costs environmental impact subsidies externalities supply chain"
- Rationale: Surface systemic impacts not visible in basic research
- Aligns with project goal of revealing invisible threads between choices and impacts

**asyncio.gather with return_exceptions=True**
- Rationale: Both option searches can run in parallel, reducing latency by ~50%
- Pattern: Graceful handling of partial failures - if one search fails, other still returns
- Benefits: Speed + resilience

**search_depth="basic" for balanced performance**
- Rationale: Phase 2 research showed "basic" provides good quality at faster speed than "advanced"
- max_results=10 for source diversity without overwhelming downstream LLM processing

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all dependencies installed cleanly, all imports verified successfully.

## User Setup Required

**External services require manual configuration.** Before using Tavily search:

1. **Tavily API Key** (required for web search)
   - Sign up at https://app.tavily.com/home
   - Copy API key from dashboard
   - Set environment variable: `TAVILY_API_KEY=tvly-...`

2. **Anthropic API Key** (required for next plan)
   - Sign up at https://console.anthropic.com/
   - Create API key
   - Set environment variable: `ANTHROPIC_API_KEY=sk-ant-...`

Verification:
```bash
cd backend
python -c "from app.services.config import get_tavily_client; get_tavily_client()"
```

Should succeed without ValueError.

## Next Phase Readiness

**Ready for 02-02 (Criteria Discovery):**
- Tavily service can fetch web sources for both options in parallel
- SearchResult and OptionResearch dataclasses ready for downstream processing
- API clients configured and cached for efficient reuse

**Ready for 02-03 (LLM Orchestration):**
- Anthropic client initialized and ready for structured output requests
- Service layer pattern established for clean integration

**No blockers** - All dependencies installed, all imports verified.

---
*Phase: 02-ai-integration-async-orchestration*
*Completed: 2026-02-07*
