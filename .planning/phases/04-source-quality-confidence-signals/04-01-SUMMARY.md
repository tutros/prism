---
phase: 04-source-quality-confidence-signals
plan: 01
subsystem: api
tags: [pydantic, source-quality, confidence, classification, claude-api]

# Dependency graph
requires:
  - phase: 02-ai-integration-async-orchestration
    provides: claude_service.py with CriteriaOutput and orchestrator.py pipeline
provides:
  - SourceMetadata model with quality tier classification
  - confidence field on Criterion (high/medium/low)
  - source_metadata dict on ComparisonResult keyed by URL
  - Extended Claude prompt with rule 6 source classification instructions
  - compute_confidence() function in orchestrator
affects:
  - frontend phases rendering confidence badges
  - phase 5 optimization (source quality data available for filtering)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Fallback-before-validate: inject missing optional fields into parsed JSON before model_validate() to guarantee backward compatibility"
    - "Quality rank map: int-ranked dict for quality tiers enables threshold comparisons in compute_confidence"

key-files:
  created: []
  modified:
    - backend/app/models.py
    - backend/app/services/claude_service.py
    - backend/app/services/orchestrator.py

key-decisions:
  - "confidence='low' default on Criterion ensures all existing JSON files load without migration"
  - "source_metadata={} default on ComparisonResult ensures all existing JSON files load without migration"
  - "Fallback for missing source_classifications inserted before model_validate() so it applies even when Claude omits the field"
  - "compute_confidence uses source count (>=2) AND quality rank threshold: high requires peer-reviewed or government; medium requires industry or news"
  - "Quality validation on source_classifications: any unrecognized quality string maps to 'unknown' before creating SourceMetadata"

patterns-established:
  - "Source quality tiers: peer-reviewed > government > industry > news > blog/unknown"
  - "Confidence thresholds: high = count>=2 AND rank>=3; medium = count>=1 AND rank>=1; low = otherwise"

# Metrics
duration: 3min
completed: 2026-02-11
---

# Phase 4 Plan 01: Source Quality + Confidence Signals Summary

**SourceMetadata model with 6-tier quality classification, confidence scoring per criterion (high/medium/low), and extended Claude prompt that classifies every cited URL during criteria generation**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-02-11T02:30:42Z
- **Completed:** 2026-02-11T02:32:51Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Added SourceMetadata Pydantic model (quality, flagged, last_verified) with all defaults for backward compatibility
- Extended Criterion with `confidence` field (default "low") and ComparisonResult with `source_metadata` dict (default {})
- Extended Claude prompt with rule 6 instructing the model to classify each cited URL by quality tier
- Added SourceClassification model and extended CriteriaOutput with `source_classifications` field
- Added fallback injection of empty `source_classifications` before `model_validate()` to handle older AI responses
- Implemented `compute_confidence()` in orchestrator using quality rank thresholds and source count
- Orchestrator now builds `source_metadata` dict from classifications and computes `confidence` per criterion

## Task Commits

Each task was committed atomically:

1. **Task 1: Add SourceMetadata model and extend Criterion/ComparisonResult** - `d16e17d` (feat)
2. **Task 2: Extend Claude prompt for source classification and add confidence calculation** - `8123601` (feat)

**Plan metadata:** (pending docs commit)

## Files Created/Modified
- `backend/app/models.py` - Added SourceMetadata model; confidence field on Criterion; source_metadata dict on ComparisonResult
- `backend/app/services/claude_service.py` - Added SourceClassification model; extended CriteriaOutput; added rule 6 to prompt; updated JSON example; added fallback before model_validate()
- `backend/app/services/orchestrator.py` - Added _QUALITY_RANK map; added compute_confidence(); builds source_metadata from classifications; assigns confidence per criterion; populates source_metadata on ComparisonResult

## Decisions Made
- Fallback for missing `source_classifications` injected into parsed dict BEFORE `model_validate()` so it handles any JSON the AI might return without the field (older cached responses, edge cases)
- `compute_confidence` uses both source count (>=2 for high) AND quality rank (peer-reviewed/government = rank 3-4 = high; industry/news = rank 1-2 = medium; blog/unknown = rank 0 = low)
- Quality validation: unrecognized quality strings from Claude map to "unknown" before constructing SourceMetadata
- All new fields have defaults (backward compatible with all existing JSON files in data/)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Source quality metadata and confidence levels are now stored in ComparisonResult JSON
- Frontend can read `criteria[i].confidence` and `source_metadata` from the API response
- Ready to build confidence badge UI components in a future plan
- No blockers

---
*Phase: 04-source-quality-confidence-signals*
*Completed: 2026-02-11*
