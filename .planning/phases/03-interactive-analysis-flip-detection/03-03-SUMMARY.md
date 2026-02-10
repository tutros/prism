# Summary: 03-03 Flip Detection and Inline Editing

## Status: Complete

## What Was Built

Implemented flip detection with actionable suggestions, sensitivity analysis, and inline criteria editing - the key differentiator of the tool.

### Deliverables

1. **Flip detection service** (backend/app/services/flip_service.py)
   - `calculate_sensitivity()` - Scores 0-1 based on |score_diff| × weight
   - `calculate_flip_analysis()` - Finds criteria where loser outperforms, calculates required weight increase
   - `generate_actionable_suggestions()` - AI transforms math into user-friendly suggestions with sources

2. **Flip analysis endpoint** (backend/app/routers/comparison.py)
   - `GET /api/comparisons/{id}/flip-analysis` - Returns suggestions and sensitivity map
   - Uses cached research for AI suggestions, falls back to basic suggestions if unavailable

3. **Flip analysis models** (backend/app/models.py)
   - `FlipSuggestionModel`, `ActionableSuggestionModel`, `FlipAnalysisResponse`

4. **FlipAnalysis component** (frontend/src/features/flip/FlipAnalysis.tsx)
   - Shows "What would make [loser] win?" with actionable cards
   - Amber styling, source citations as links
   - "No realistic way to flip" message when no suggestions available
   - Uses placeholderData to prevent flickering

5. **CriteriaEditor component** (frontend/src/features/criteria/CriteriaEditor.tsx)
   - Click to edit name, scores inline
   - Optimistic updates with rollback on error
   - Sensitivity badges (High Impact / Medium Impact)
   - Custom badge for user-created criteria

6. **AddCriterion component** (frontend/src/features/criteria/AddCriterion.tsx)
   - "+ Add Custom Criterion" button expands to form
   - Creates criterion with origin="user"

7. **Updated ScoringExplainer** - Added impact badges explanation

## Commits

| Hash | Description |
|------|-------------|
| 2929371 | feat(03-03): add flip detection service with sensitivity analysis |
| ba9b788 | feat(03-03): add flip analysis endpoint |
| b03f942 | feat(03-03): add FlipAnalysis, CriteriaEditor, and AddCriterion components |
| 96f458c | fix(03-03): fix apiPost/apiGet usage - already returns parsed JSON |
| a8aef62 | fix(03-03): use correct query key 'comparison' not 'results' |
| 9461289 | fix(03-03): add API_BASE to CriteriaEditor fetch call |
| dc9afff | docs(03-03): add impact badges explanation to scoring explainer |
| 65afc4a | fix(03-03): prevent flickering on weight change, improve no-flip message |

## Verification

- User-approved checkpoint
- All features tested: Go Deeper, Regenerate Weights, Flip Analysis, Inline Editing, Custom Criteria, Sensitivity Badges

## Key Decisions

- Flip analysis uses stored weights (not slider values) to avoid excessive AI calls
- placeholderData prevents UI flickering during refetch
- Sensitivity threshold: >0.7 = High Impact, >0.4 = Medium Impact
- "No realistic way to flip" shown when winner dominates all criteria
