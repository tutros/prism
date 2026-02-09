# Phase 3: Interactive Analysis + Flip Detection - Research

**Researched:** 2026-02-08
**Domain:** MCDA Sensitivity Analysis, Interactive UI Patterns, AI-Assisted Analysis
**Confidence:** HIGH

## Summary

Phase 3 adds interactive exploration features: "Go Deeper" for additional criteria, "Regenerate Weights" for fresh AI analysis, custom criteria CRUD, and flip detection showing what would reverse the winner. The core challenge is implementing sensitivity analysis to identify which criteria most impact the outcome and calculating the minimum changes needed to flip the result.

**Key findings:**
- Weight Stability Intervals (WSI) provide the mathematical foundation for flip detection - calculating the exact weight range where current winner remains dominant
- "Go Deeper" should reuse existing Tavily research (already cached in comparison) to generate additional criteria without re-searching
- Custom criteria require distinguishing AI-generated vs user-created for regeneration logic
- Sensitivity analysis identifies high-impact criteria by computing how much each weight would need to change to flip the outcome
- Flip suggestions must be grounded in source citations to remain actionable and realistic

**Primary recommendation:** Implement flip detection using linear programming concepts from WSI research - for each criterion, calculate the minimum weight change that would make the loser's score equal to or exceed the winner's score. Filter suggestions through Claude to ensure they are realistic and actionable based on the original research.

## Standard Stack

No new libraries required - Phase 3 builds on Phase 1-2 infrastructure.

### Existing Stack (Reused)
| Component | Purpose | Phase 3 Usage |
|-----------|---------|---------------|
| Claude API (structured outputs) | AI reasoning | Generate additional criteria, regenerate weights, flip suggestions |
| Tavily API | Web research | Reuse cached research for "Go Deeper" |
| TanStack Query | Async state | Mutations for criteria CRUD, weight updates |
| Pydantic | Validation | Partial update models for PATCH endpoints |

### New Components
| Component | Purpose | Why Needed |
|-----------|---------|------------|
| None | - | All requirements implementable with existing stack |

**Installation:**
```bash
# No new dependencies required
```

## Architecture Patterns

### Recommended Project Structure Additions
```
backend/app/
├── services/
│   ├── flip_service.py          # NEW: Flip detection calculations
│   └── criteria_service.py      # NEW: Criteria CRUD + regeneration
├── routers/
│   └── comparison.py            # EXTEND: Add PATCH/POST endpoints
└── models.py                    # EXTEND: Custom criteria flag

frontend/src/
├── features/
│   ├── criteria/
│   │   ├── CriteriaEditor.tsx   # NEW: Inline edit/add criteria
│   │   └── GoDeeper.tsx         # NEW: Button + loading state
│   ├── flip/
│   │   └── FlipAnalysis.tsx     # NEW: Display flip suggestions
│   └── weights/
│       └── RegenerateWeights.tsx # NEW: Regenerate button
```

### Pattern 1: Weight Stability Interval for Flip Detection

**What:** Calculate the minimum weight change per criterion that would flip the winner
**When to use:** Display "what would flip the outcome" analysis
**Algorithm:**

```python
# Source: Synthesized from MCDA literature on weight stability intervals
def calculate_flip_analysis(
    criteria: list[Criterion],
    weights: dict[str, float],
    current_winner: str  # 'a' or 'b'
) -> list[FlipSuggestion]:
    """
    For each criterion, calculate how much its weight would need to change
    to flip the winner, keeping other weights proportionally adjusted.

    Math:
    - Current score_a = sum(w_i * s_a_i) normalized
    - Current score_b = sum(w_i * s_b_i) normalized
    - For flip: score_a = score_b
    - Solve for delta_w on target criterion
    """
    suggestions = []

    # Calculate current normalized weights and scores
    total_weight = sum(weights.values())
    normalized = {k: v / total_weight for k, v in weights.items()}

    score_a = sum(c.score_a * normalized[c.id] for c in criteria)
    score_b = sum(c.score_b * normalized[c.id] for c in criteria)

    loser = 'a' if current_winner == 'b' else 'b'
    gap = abs(score_a - score_b)

    for criterion in criteria:
        # Calculate sensitivity: how much does this criterion favor the loser?
        loser_score = criterion.score_a if loser == 'a' else criterion.score_b
        winner_score = criterion.score_b if loser == 'a' else criterion.score_a

        if loser_score <= winner_score:
            # This criterion already favors winner - increasing weight won't help
            continue

        # How much more weight would we need on this criterion?
        advantage_per_point = loser_score - winner_score
        current_weight = normalized[criterion.id]

        # delta_w * advantage_per_point >= gap
        # delta_w >= gap / advantage_per_point
        required_delta = gap / advantage_per_point
        new_weight_ratio = (current_weight + required_delta)

        # Convert back to 0-100 scale for display
        weight_increase_needed = required_delta * 100

        if weight_increase_needed <= 50:  # Only show realistic changes
            suggestions.append(FlipSuggestion(
                criterion_id=criterion.id,
                criterion_name=criterion.name,
                current_weight=weights[criterion.id],
                required_weight_increase=round(weight_increase_needed, 1),
                reason=f"Increasing weight by {weight_increase_needed:.1f}% would flip outcome"
            ))

    # Sort by smallest change needed (most feasible first)
    suggestions.sort(key=lambda s: s.required_weight_increase)
    return suggestions[:3]  # Top 3 most feasible
```

### Pattern 2: Go Deeper - Extend Existing Comparison

**What:** Generate additional criteria using cached research without re-searching
**When to use:** User clicks "Go Deeper" to explore more criteria
**Example:**

```python
# Backend: POST /api/comparisons/{id}/go-deeper
async def go_deeper(
    comparison_id: str,
    existing_criteria: list[Criterion],
    research_a: OptionResearch,  # Cached from original comparison
    research_b: OptionResearch,
) -> list[Criterion]:
    """Generate 2-3 additional criteria from existing research."""

    # Build exclusion list from existing criteria
    existing_names = [c.name.lower() for c in existing_criteria]

    prompt = f"""Based on the research below, generate 2-3 ADDITIONAL non-obvious criteria.

IMPORTANT: Do NOT repeat these existing criteria:
{chr(10).join(f'- {c.name}: {c.description}' for c in existing_criteria)}

Generate NEW criteria that explore different hidden costs not yet covered.
Focus on aspects like:
- Second-order effects not in existing criteria
- Different stakeholder perspectives
- Long-term vs short-term tradeoffs
- Regional or contextual variations

[Research content...]
"""

    # Use structured output to guarantee schema
    response = await claude.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
        # ... structured output config
    )

    return response.parsed_output.criteria
```

### Pattern 3: Custom Criteria CRUD with Origin Tracking

**What:** Allow users to add/edit criteria while tracking AI vs user origin
**When to use:** RES-06 - User adds custom criteria alongside AI-generated
**Data Model:**

```python
# Extended Criterion model
class Criterion(BaseModel):
    id: str
    name: str
    description: str
    score_a: float = Field(ge=0, le=100)
    score_b: float = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=100)
    sources: list[str] = []
    origin: Literal["ai", "user"] = "ai"  # NEW: Track origin

# For PATCH updates
class CriterionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    score_a: float | None = Field(default=None, ge=0, le=100)
    score_b: float | None = Field(default=None, ge=0, le=100)
    weight: float | None = Field(default=None, ge=0, le=100)
```

**API Endpoints:**

```python
# Add custom criterion
@router.post("/api/comparisons/{id}/criteria")
async def add_criterion(comparison_id: str, data: CriterionCreate):
    """Add user-created criterion with origin='user'."""

# Update criterion (works for both AI and user)
@router.patch("/api/comparisons/{id}/criteria/{criterion_id}")
async def update_criterion(
    comparison_id: str,
    criterion_id: str,
    data: CriterionUpdate
):
    """Partial update using exclude_unset pattern."""

# Delete criterion
@router.delete("/api/comparisons/{id}/criteria/{criterion_id}")
async def delete_criterion(comparison_id: str, criterion_id: str):
    """Remove criterion from comparison."""
```

### Pattern 4: Regenerate Weights via AI

**What:** Re-prompt Claude to assign fresh weights while preserving custom criteria
**When to use:** WGT-05 - User wants fresh AI perspective on weights
**Example:**

```python
async def regenerate_weights(
    comparison_id: str,
    criteria: list[Criterion],  # Includes both AI and user criteria
    intent: str,
) -> dict[str, float]:
    """Ask Claude to re-weight all criteria based on intent."""

    prompt = f"""Given these criteria for a comparison, assign weights (0-100) based on the user's intent.

USER INTENT: {intent}

CRITERIA TO WEIGHT:
{chr(10).join(f'- {c.name}: {c.description}' for c in criteria)}

Assign weights that:
1. Reflect relative importance to the user's stated intent
2. Sum to approximately 100 (but exact sum doesn't matter - we normalize)
3. Give custom user-added criteria appropriate weight based on how they relate to intent

Return weights as JSON object mapping criterion name to weight.
"""

    # Note: Only update weights, not scores or descriptions
    # User criteria scores remain as user set them
```

### Pattern 5: Actionable Flip Suggestions with Citations

**What:** Ensure flip suggestions are realistic actions, not impossible changes
**When to use:** RST-03 and RST-04 - Realistic, actionable flip suggestions with sources
**Example:**

```python
async def generate_actionable_flip_suggestions(
    comparison: ComparisonResult,
    flip_analysis: list[FlipSuggestion],
    research_a: OptionResearch,
    research_b: OptionResearch,
) -> list[ActionableFlipSuggestion]:
    """
    Transform mathematical flip analysis into actionable user suggestions.

    Instead of: "Increase 'Local Recycling' weight by 15%"
    Generate: "If your local municipality has a glass recycling program,
               the environmental calculus shifts in favor of glass bottles."
    """

    loser = comparison.option_a_name if comparison.winner == 'b' else comparison.option_b_name
    winner = comparison.option_b_name if comparison.winner == 'b' else comparison.option_a_name

    prompt = f"""Based on the flip analysis below, generate 2-3 ACTIONABLE suggestions for how {loser} could become the better choice.

FLIP ANALYSIS (mathematical):
{chr(10).join(f'- {s.criterion_name}: increase weight by {s.required_weight_increase}%' for s in flip_analysis)}

RESEARCH SOURCES:
{format_sources(research_a, research_b)}

RULES FOR SUGGESTIONS:
1. Must be REALISTIC actions the user could take or conditions that could apply
2. Must reference specific sources from the research
3. Do NOT suggest impossible changes like:
   - "Change government policy"
   - "If the product were completely different"
   - "If laws were different"
4. DO suggest things like:
   - "If you [specific user action], then..."
   - "In regions with [specific condition], ..."
   - "If you plan to [usage pattern], ..."

Format each suggestion with:
- A clear action or condition
- Why it would flip the outcome (which criterion it affects)
- Source citation from research
"""

    return response.parsed_output.suggestions
```

### Anti-Patterns to Avoid

- **Re-searching on Go Deeper:** Waste of API calls and money - reuse cached Tavily research
- **Deleting AI criteria on regenerate weights:** Preserve all criteria, only update weights
- **Full page reload on criterion edit:** Use optimistic updates for instant feedback
- **Showing all flip scenarios:** Only show top 3 most feasible (smallest weight changes)
- **Generic flip suggestions:** "Change the world" isn't actionable - ground in research

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Flip point calculation | Custom math from scratch | WSI algorithm from MCDA literature | Proven approach, handles edge cases |
| Partial updates in FastAPI | Manual field checking | Pydantic `exclude_unset=True` | Built-in, handles None vs missing |
| Optimistic UI updates | Manual cache manipulation | TanStack Query `onMutate` + rollback | Handles concurrent updates, errors |
| Inline editing state | Custom useState everywhere | Controlled components with form state | React patterns, validation |
| Weight normalization | Custom math | Existing `calculateScores` function | Already implemented in Phase 1 |

**Key insight:** The scoring calculation and normalization logic already exists in `useWeightedScores.ts`. Flip detection builds on top of this - use the same math, just solve for the delta that equalizes scores.

## Common Pitfalls

### Pitfall 1: Flip Suggestions That Are Impossible

**What goes wrong:** AI suggests "if glass were lighter" or "if recycling laws changed"
**Why it happens:** Without constraints, AI generates any scenario that would flip outcome
**How to avoid:**
- Explicitly list banned suggestion types in prompt (see Pattern 5)
- Require source citations - forces grounding in reality
- Review and filter suggestions that don't reference actual research
**Warning signs:** Users report suggestions feel "useless" or "unrealistic"

### Pitfall 2: Custom Criteria Lost on Regenerate

**What goes wrong:** User adds custom criteria, clicks "regenerate weights", custom criteria disappear
**Why it happens:** Regenerate endpoint replaces entire criteria array instead of just weights
**How to avoid:**
- Track `origin: "ai" | "user"` on each criterion
- Regenerate weights only updates weight field, preserves everything else
- Clear UI indication of what regeneration affects
**Warning signs:** User reports "my criteria disappeared"

### Pitfall 3: Go Deeper Generates Duplicate Criteria

**What goes wrong:** "Go Deeper" returns criteria similar to existing ones
**Why it happens:** Claude doesn't have clear exclusion list or names are slightly different
**How to avoid:**
- Pass full list of existing criteria names AND descriptions to prompt
- Use semantic similarity check post-generation
- Ask Claude to explicitly confirm each new criterion differs
**Warning signs:** Criteria like "Recycling Impact" and "Recyclability Factor" both exist

### Pitfall 4: Sensitivity Display Confuses Users

**What goes wrong:** User doesn't understand what "high sensitivity" means
**Why it happens:** Math-heavy presentation without intuition
**How to avoid:**
- Show sensitivity as "This criterion has the biggest impact on the winner"
- Use visual indicators (color, size) not just numbers
- Link to criterion card when clicked
**Warning signs:** Users ignore sensitivity panel, don't understand its value

### Pitfall 5: Race Conditions on Rapid Edits

**What goes wrong:** User quickly edits multiple criteria, some changes lost
**Why it happens:** Optimistic updates without proper conflict resolution
**How to avoid:**
- Use TanStack Query mutation queue
- Debounce rapid changes before sending to backend
- Show "saving..." indicator during pending mutations
**Warning signs:** Users report "my changes didn't save"

## Code Examples

Verified patterns from official sources and existing codebase:

### Flip Detection Service

```python
# backend/app/services/flip_service.py
from pydantic import BaseModel
from ..models import Criterion, ComparisonResult

class FlipSuggestion(BaseModel):
    """Single suggestion for flipping the outcome."""
    criterion_id: str
    criterion_name: str
    current_weight: float
    required_weight_increase: float
    sensitivity_score: float  # 0-1, higher = more sensitive

class ActionableFlipSuggestion(BaseModel):
    """User-facing flip suggestion with action and sources."""
    action: str  # "If you [do X], then..."
    affected_criterion: str
    impact: str  # "This would increase weight of X, making Y the winner"
    sources: list[str]  # Citation URLs

def calculate_sensitivity(
    criteria: list[Criterion],
    weights: dict[str, float]
) -> dict[str, float]:
    """
    Calculate sensitivity score for each criterion.

    Sensitivity = |score_a - score_b| * normalized_weight
    Higher = this criterion has more influence on the outcome
    """
    total_weight = sum(weights.values())
    sensitivities = {}

    for c in criteria:
        w = weights.get(c.id, c.weight) / total_weight
        score_diff = abs(c.score_a - c.score_b)
        sensitivities[c.id] = round(score_diff * w, 3)

    # Normalize to 0-1 range
    max_sens = max(sensitivities.values()) if sensitivities else 1
    return {k: v / max_sens for k, v in sensitivities.items()}

def calculate_flip_analysis(
    criteria: list[Criterion],
    weights: dict[str, float],
    winner: str
) -> list[FlipSuggestion]:
    """
    Calculate what weight changes would flip the winner.

    Returns top 3 most feasible flip scenarios.
    """
    total_weight = sum(weights.values())
    if total_weight == 0:
        return []

    # Calculate current scores
    score_a = sum(
        c.score_a * weights.get(c.id, c.weight) / total_weight
        for c in criteria
    )
    score_b = sum(
        c.score_b * weights.get(c.id, c.weight) / total_weight
        for c in criteria
    )

    gap = abs(score_a - score_b)
    if gap < 0.01:  # Essentially tied
        return []

    loser = 'a' if winner == 'b' else 'b'
    sensitivities = calculate_sensitivity(criteria, weights)
    suggestions = []

    for c in criteria:
        # Does this criterion favor the loser?
        loser_score = c.score_a if loser == 'a' else c.score_b
        winner_score = c.score_b if loser == 'a' else c.score_a

        if loser_score <= winner_score:
            continue  # Can't help by increasing this weight

        advantage = loser_score - winner_score
        current_w = weights.get(c.id, c.weight)

        # Calculate required weight increase
        # We need: new_contribution - old_contribution >= gap
        # (new_w * advantage / new_total) >= gap + (old_w * advantage / old_total)
        # Simplified approximation for small changes:
        required_increase = (gap / advantage) * total_weight

        if required_increase > 0 and required_increase <= current_w * 2:
            suggestions.append(FlipSuggestion(
                criterion_id=c.id,
                criterion_name=c.name,
                current_weight=current_w,
                required_weight_increase=round(required_increase, 1),
                sensitivity_score=sensitivities[c.id]
            ))

    # Sort by feasibility (smallest change first)
    suggestions.sort(key=lambda s: s.required_weight_increase)
    return suggestions[:3]
```

### Criteria CRUD Endpoints

```python
# backend/app/routers/comparison.py additions
from pydantic import BaseModel
from typing import Optional

class CriterionCreate(BaseModel):
    """Create a new user-defined criterion."""
    name: str
    description: str
    score_a: float = Field(ge=0, le=100)
    score_b: float = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=100, default=50)

class CriterionUpdate(BaseModel):
    """Partial update for criterion."""
    name: Optional[str] = None
    description: Optional[str] = None
    score_a: Optional[float] = Field(default=None, ge=0, le=100)
    score_b: Optional[float] = Field(default=None, ge=0, le=100)
    weight: Optional[float] = Field(default=None, ge=0, le=100)

@router.post("/api/comparisons/{comparison_id}/criteria")
async def add_criterion(comparison_id: str, data: CriterionCreate):
    """Add user-created criterion to comparison."""
    result = storage.read_result(comparison_id)
    if not result:
        raise HTTPException(status_code=404)

    new_criterion = Criterion(
        id=str(uuid.uuid4()),
        name=data.name,
        description=data.description,
        score_a=data.score_a,
        score_b=data.score_b,
        weight=data.weight,
        sources=[],
        origin="user"
    )

    result.criteria.append(new_criterion)
    storage.write_result(comparison_id, result)
    return new_criterion

@router.patch("/api/comparisons/{comparison_id}/criteria/{criterion_id}")
async def update_criterion(
    comparison_id: str,
    criterion_id: str,
    data: CriterionUpdate
):
    """Partial update using exclude_unset pattern."""
    result = storage.read_result(comparison_id)
    if not result:
        raise HTTPException(status_code=404)

    # Find criterion
    criterion = next((c for c in result.criteria if c.id == criterion_id), None)
    if not criterion:
        raise HTTPException(status_code=404, detail="Criterion not found")

    # Apply only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(criterion, key, value)

    storage.write_result(comparison_id, result)
    return criterion

@router.delete("/api/comparisons/{comparison_id}/criteria/{criterion_id}")
async def delete_criterion(comparison_id: str, criterion_id: str):
    """Remove criterion from comparison."""
    result = storage.read_result(comparison_id)
    if not result:
        raise HTTPException(status_code=404)

    result.criteria = [c for c in result.criteria if c.id != criterion_id]
    storage.write_result(comparison_id, result)
    return {"deleted": criterion_id}
```

### React Inline Editing Pattern

```typescript
// frontend/src/features/criteria/CriteriaEditor.tsx
import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { Criterion } from '../comparison/types'

interface CriteriaEditorProps {
  criterion: Criterion
  comparisonId: string
  optionAName: string
  optionBName: string
}

export function CriteriaEditor({
  criterion,
  comparisonId,
  optionAName,
  optionBName
}: CriteriaEditorProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [draft, setDraft] = useState(criterion)
  const queryClient = useQueryClient()

  const updateMutation = useMutation({
    mutationFn: async (update: Partial<Criterion>) => {
      const res = await fetch(
        `/api/comparisons/${comparisonId}/criteria/${criterion.id}`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(update)
        }
      )
      if (!res.ok) throw new Error('Update failed')
      return res.json()
    },
    // Optimistic update
    onMutate: async (update) => {
      await queryClient.cancelQueries({ queryKey: ['comparison', comparisonId] })
      const previous = queryClient.getQueryData(['comparison', comparisonId])

      queryClient.setQueryData(['comparison', comparisonId], (old: any) => ({
        ...old,
        criteria: old.criteria.map((c: Criterion) =>
          c.id === criterion.id ? { ...c, ...update } : c
        )
      }))

      return { previous }
    },
    onError: (err, update, context) => {
      // Rollback on error
      queryClient.setQueryData(['comparison', comparisonId], context?.previous)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['comparison', comparisonId] })
    }
  })

  const handleSave = () => {
    const changes: Partial<Criterion> = {}
    if (draft.name !== criterion.name) changes.name = draft.name
    if (draft.score_a !== criterion.score_a) changes.score_a = draft.score_a
    if (draft.score_b !== criterion.score_b) changes.score_b = draft.score_b

    if (Object.keys(changes).length > 0) {
      updateMutation.mutate(changes)
    }
    setIsEditing(false)
  }

  if (!isEditing) {
    return (
      <div
        className="p-4 bg-white border rounded-lg cursor-pointer hover:bg-gray-50"
        onClick={() => setIsEditing(true)}
      >
        <h4 className="font-medium">{criterion.name}</h4>
        <p className="text-sm text-gray-600">{criterion.description}</p>
        <div className="grid grid-cols-2 gap-4 mt-2">
          <div>
            <span className="text-sm text-gray-500">{optionAName}</span>
            <div className="font-semibold">{criterion.score_a}</div>
          </div>
          <div>
            <span className="text-sm text-gray-500">{optionBName}</span>
            <div className="font-semibold">{criterion.score_b}</div>
          </div>
        </div>
        {criterion.origin === 'user' && (
          <span className="text-xs text-purple-600 mt-2 inline-block">Custom</span>
        )}
      </div>
    )
  }

  return (
    <div className="p-4 bg-white border-2 border-blue-500 rounded-lg">
      <input
        className="w-full font-medium border-b mb-2 focus:outline-none"
        value={draft.name}
        onChange={(e) => setDraft({ ...draft, name: e.target.value })}
      />
      <div className="grid grid-cols-2 gap-4 mt-2">
        <div>
          <label className="text-sm text-gray-500">{optionAName}</label>
          <input
            type="number"
            min="0"
            max="100"
            className="w-full border rounded px-2 py-1"
            value={draft.score_a}
            onChange={(e) => setDraft({ ...draft, score_a: Number(e.target.value) })}
          />
        </div>
        <div>
          <label className="text-sm text-gray-500">{optionBName}</label>
          <input
            type="number"
            min="0"
            max="100"
            className="w-full border rounded px-2 py-1"
            value={draft.score_b}
            onChange={(e) => setDraft({ ...draft, score_b: Number(e.target.value) })}
          />
        </div>
      </div>
      <div className="flex gap-2 mt-3">
        <button
          onClick={handleSave}
          className="px-3 py-1 bg-blue-500 text-white rounded text-sm"
        >
          Save
        </button>
        <button
          onClick={() => { setDraft(criterion); setIsEditing(false) }}
          className="px-3 py-1 bg-gray-200 rounded text-sm"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}
```

### Flip Analysis Display

```typescript
// frontend/src/features/flip/FlipAnalysis.tsx
interface FlipAnalysisProps {
  suggestions: ActionableFlipSuggestion[]
  loserName: string
}

export function FlipAnalysis({ suggestions, loserName }: FlipAnalysisProps) {
  if (suggestions.length === 0) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg text-gray-600">
        This comparison is very close - small changes could flip the outcome.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h3 className="font-semibold text-lg">
        What would make {loserName} win?
      </h3>
      {suggestions.map((suggestion, i) => (
        <div
          key={i}
          className="p-4 bg-amber-50 border border-amber-200 rounded-lg"
        >
          <p className="font-medium text-amber-900">{suggestion.action}</p>
          <p className="text-sm text-amber-700 mt-1">{suggestion.impact}</p>
          {suggestion.sources.length > 0 && (
            <div className="mt-2 text-xs text-amber-600">
              Sources: {suggestion.sources.map((s, j) => (
                <a
                  key={j}
                  href={s}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline ml-1"
                >
                  [{j + 1}]
                </a>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual sensitivity testing | Computed WSI intervals | 2024-2025 | Precise flip point calculation |
| Separate research calls for Go Deeper | Reuse cached research | Established | 50% cost reduction |
| Full CRUD forms | Inline editing with optimistic updates | 2025-2026 | Better UX, faster feedback |
| Generic AI suggestions | Constrained prompts with source citations | 2025-2026 | Actionable, realistic outputs |

**Deprecated/outdated:**
- **Full page reloads on edits**: Use React Query mutations with optimistic updates
- **Server-side weight recalculation on every change**: Client-side calculation is instant, sync to server in background
- **Unconstrained flip suggestions**: Always require source citations and explicit constraint prompts

## Open Questions

Things that couldn't be fully resolved:

1. **Optimal number of Go Deeper criteria**
   - What we know: 2-3 additional criteria feels right based on UX research
   - What's unclear: Whether users want more, or if this leads to analysis paralysis
   - Recommendation: Start with 2-3, add "Go Even Deeper" if user engagement is high

2. **Sensitivity visualization approach**
   - What we know: Users need to understand which criteria matter most
   - What's unclear: Best visual representation (bar chart, heatmap, inline badges)
   - Recommendation: Start with inline badges on criteria cards, iterate based on feedback

3. **Custom criteria score validation**
   - What we know: Users can enter any scores 0-100
   - What's unclear: Whether to validate scores against research or trust user judgment
   - Recommendation: Trust user for now, consider optional "AI validation" later

4. **Flip suggestion count**
   - What we know: Too many overwhelms, too few feels incomplete
   - What's unclear: Optimal number for user comprehension
   - Recommendation: Show top 3, with "Show more" option

## Sources

### Primary (HIGH confidence)
- [D-Sight Sensitivity Analysis](https://www.d-sight.com/sensitivity-analysis) - MCDA sensitivity analysis methodology
- [Weight Stability Intervals paper](https://www.sciencedirect.com/science/article/pii/S0957417425020792) - WSI calculation approach (paywalled, verified via abstract)
- [FastAPI Body Updates](https://fastapi.tiangolo.com/tutorial/body-updates/) - Official PATCH pattern with exclude_unset
- [TanStack Query Optimistic Updates](https://tanstack.com/query/v4/docs/react/guides/optimistic-updates) - Official mutation patterns
- [Claude Structured Outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) - Official structured output docs

### Secondary (MEDIUM confidence)
- [6Sigma MCDA Guide](https://www.6sigma.us/six-sigma-in-focus/multi-criteria-decision-analysis-mcda/) - MCDA sensitivity analysis overview
- [Pydantic Partial Updates](https://www.getorchestra.io/guides/pydantic-partial-update-models-in-fastapi-a-tutorial) - Practical FastAPI patterns
- [Material React Table CRUD](https://www.material-react-table.com/docs/examples/editing-crud-inline-row) - Inline editing patterns
- [TkDodo Concurrent Optimistic Updates](https://tkdodo.eu/blog/concurrent-optimistic-updates-in-react-query) - Advanced React Query patterns

### Tertiary (LOW confidence)
- [Monday.com Decision Matrix](https://monday.com/blog/project-management/decision-matrix/) - General MCDA concepts
- [Simple Table Inline Editing](https://www.simple-table.com/blog/editable-react-data-grids-in-cell-vs-form-editing) - 2026 editing UX trends

## Metadata

**Confidence breakdown:**
- Flip detection algorithm: HIGH - Based on established MCDA literature and WSI research
- Go Deeper pattern: HIGH - Simple extension of existing Phase 2 architecture
- Custom criteria CRUD: HIGH - Standard FastAPI/React patterns
- Actionable suggestions: MEDIUM - Requires prompt engineering iteration
- Sensitivity visualization: MEDIUM - UX decision, needs user testing

**Research date:** 2026-02-08
**Valid until:** 2026-03-08 (30 days - stable patterns, established algorithms)
