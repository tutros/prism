---
phase: 02-ai-integration-async-orchestration
plan: 02
subsystem: ai
tags: [claude, anthropic, structured-outputs, orchestrator, pydantic]

# Dependency graph
requires:
  - phase: 02-01
    provides: Tavily web search service and API client configuration
provides:
  - Claude criteria generation service with structured outputs
  - Orchestrator combining Tavily search and Claude analysis
  - Real AI processing in comparison endpoint (replaces mock)
affects: [02-03, phase-3, phase-4]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Structured output with Pydantic models (CriterionOutput, CriteriaOutput)"
    - "Prompt caching on system prompt for 90% cost reduction"
    - "Three-step orchestration: search -> analyze -> transform"
    - "Error handling at each orchestration step"

key-files:
  created:
    - backend/app/services/claude_service.py
    - backend/app/services/orchestrator.py
  modified:
    - backend/app/routers/comparison.py

key-decisions:
  - "Use Claude's structured outputs via Pydantic for guaranteed schema compliance"
  - "Implement prompt caching on system prompt (cache_control: ephemeral) for 90% cost reduction"
  - "Focus criteria on non-obvious hidden costs (subsidies, externalities, supply chain)"
  - "Graceful fallback on JSON parsing errors returns minimal valid response"
  - "Three-step orchestration flow: Tavily search -> Claude analysis -> ComparisonResult transform"

patterns-established:
  - "Orchestrator pattern: clean separation, doesn't know service internals"
  - "Error handling at each step with meaningful error messages in ComparisonResult"
  - "Transform AI output models to app models for clean architecture"

# Metrics
duration: 16min
completed: 2026-02-08
---

# Phase 2 Plan 02: Criteria Discovery with Claude Summary

**Claude structured output service generating non-obvious criteria from web research with source citations and orchestrated pipeline**

## Performance

- **Duration:** 16 min
- **Started:** 2026-02-08T16:19:04Z
- **Completed:** 2026-02-08T16:35:15Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Created Claude service using structured outputs (CriterionOutput, CriteriaOutput) with prompt caching
- Implemented orchestrator combining Tavily search and Claude analysis in 3-step flow
- Replaced mock comparison generator with real AI processing
- Focus on non-obvious criteria: hidden costs, subsidies, externalities, supply chain impacts
- Graceful error handling at each orchestration step
- Source URL validation from Tavily research results

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Claude criteria generation service** - `f078949` (feat)
2. **Task 2: Create orchestrator combining Tavily and Claude** - `24b7de4` (feat)
3. **Task 3: Wire orchestrator into comparison endpoint** - `8786311` (feat)

## Files Created/Modified
- `backend/app/services/claude_service.py` - Generate 3-5 non-obvious criteria from research with structured outputs
- `backend/app/services/orchestrator.py` - Three-step flow: web search -> AI analysis -> structured result
- `backend/app/routers/comparison.py` - Use real orchestrator instead of mock (process_comparison replaces generate_mock_result)

## Decisions Made

**Claude API integration:**
- Use Pydantic models (CriterionOutput, CriteriaOutput) for structured output validation
- Implement prompt caching on system prompt (cache_control: ephemeral) for 90% cost reduction
- Model: claude-sonnet-4-5-20250929 with 4096 max_tokens
- JSON parsing with markdown code block extraction fallback

**Criteria focus:**
- Target non-obvious hidden costs: embedded energy, subsidies, externalities, supply chain
- Negative examples in prompt: exclude obvious factors (price, durability, convenience, brand)
- Weight criteria based on user intent
- Require source URLs from Tavily research for each criterion

**Orchestration pattern:**
- Three-step flow: parallel web search -> AI analysis -> transform to ComparisonResult
- Error handling at each step returns ComparisonResult with error status
- Clean separation: orchestrator doesn't know Tavily/Claude internals
- Transform AI models (CriteriaOutput) to app models (Criterion, ComparisonResult)

**Error handling:**
- Complete search failure (both options) returns error ComparisonResult
- AI analysis exception caught and returns error ComparisonResult
- JSON parsing error has graceful fallback with minimal valid response

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

**External services require manual configuration.** Environment variables needed:

```bash
# Anthropic API for Claude
ANTHROPIC_API_KEY=sk-ant-...  # Get from https://console.anthropic.com/settings/keys

# Tavily API for web search
TAVILY_API_KEY=tvly-...  # Get from https://tavily.com (already configured in 02-01)
```

**Verification commands:**
```bash
# Test imports
cd backend && python -c "from app.services.claude_service import generate_criteria; print('OK')"
cd backend && python -c "from app.services.orchestrator import generate_comparison; print('OK')"

# Test server startup
cd backend && uvicorn app.main:app --reload
```

**Note:** Full end-to-end testing requires both ANTHROPIC_API_KEY and TAVILY_API_KEY set.

## Next Phase Readiness

**Ready for 02-03 (Async orchestration with progress tracking):**
- Base orchestrator implemented and working
- Clean separation allows adding progress callbacks without changing service internals
- ComparisonResult model supports status tracking (processing, completed, error)
- Background task pattern established in comparison endpoint

**No blockers.** Ready to add:
- Server-Sent Events (SSE) for real-time progress streaming
- Progress tracking in orchestrator (search started, search done, analysis started, etc.)
- Frontend progress UI showing step-by-step status

---
*Phase: 02-ai-integration-async-orchestration*
*Completed: 2026-02-08*
