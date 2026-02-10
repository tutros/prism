# Summary: 03-02 Go Deeper and Regenerate Weights

## Status: Complete

## What Was Built

Added Go Deeper and Regenerate Weights features allowing users to explore additional criteria and get fresh AI weight assignments.

### Deliverables

1. **Criteria service** (backend/app/services/criteria_service.py)
   - `go_deeper()` - Generates 2-3 additional non-obvious criteria using cached research
   - `regenerate_weights()` - AI assigns weights based on user intent
   - Uses structured output with JSON parsing fallback
   - Prompt caching on system prompts for cost reduction

2. **Research caching** (backend/app/models.py, orchestrator.py)
   - Added `research_a` and `research_b` fields to ComparisonResult
   - Orchestrator saves research as dict using `dataclasses.asdict()`
   - Enables Go Deeper without re-running web search

3. **New endpoints** (backend/app/routers/comparison.py)
   - `POST /api/comparisons/{id}/go-deeper` - Appends new criteria
   - `POST /api/comparisons/{id}/regenerate-weights` - Updates all weights
   - Returns 400 if research not cached (MVP behavior)

4. **Frontend components**
   - `GoDeeper.tsx` - Button with loading spinner, triggers mutation
   - `RegenerateWeights.tsx` - Button with loading spinner, triggers mutation
   - Updated `ResultsDisplay.tsx` with buttons and origin badges

## Commits

| Hash | Description |
|------|-------------|
| 4cc4e26 | feat(03-02): add criteria service for Go Deeper and Regenerate Weights |
| c8d2bbf | feat(03-02): add go-deeper and regenerate-weights endpoints |
| 6ddc11c | feat(03-02): add Go Deeper and Regenerate Weights buttons |

## Verification

- TypeScript compiles without errors
- Backend imports work correctly
- Both endpoints return updated comparison result
- Buttons show loading state during mutation

## Key Decisions

- Research cached as dict (serializable for JSON storage)
- Go Deeper excludes existing criteria by name/description
- Regenerate Weights maps by criterion name then translates to ID
- Default weight of 50 if AI misses a criterion
