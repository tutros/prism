# Phase 4: Source Quality + Confidence Signals - Research

**Researched:** 2026-02-10
**Domain:** Source metadata modeling, AI classification prompting, React badge UI patterns
**Confidence:** HIGH

## Summary

Phase 4 adds trustworthiness signals to the existing source citations already displayed in `CriteriaEditor`. The infrastructure is already complete: sources are stored as `list[str]` (URLs) on each `Criterion`, displayed as inline links in `CriteriaEditor.tsx`, and persisted in JSON via `JSONStorage`. This phase extends that data model and display.

The scope is surgical: add a `SourceMetadata` model alongside (not replacing) the existing `sources: list[str]`, extend the Claude prompt to classify sources during generation, add a flag toggle endpoint, and update `CriteriaEditor` to show quality badges + flag icons. No new libraries are required. No new services or orchestration patterns are needed.

The primary design decisions are locked: AI classification via Claude (no domain heuristics), Text Badges (High/Medium/Low) for confidence, Inline Links (comma-separated) for multi-source display, and Click Icon flag toggle for user flagging.

**Primary recommendation:** Add a `source_metadata: dict[str, SourceMetadata]` field to `ComparisonResult` keyed by URL. This keeps `sources: list[str]` on `Criterion` unchanged (backward compatible) while adding enrichment separately. The Claude prompt extension in `generate_criteria` outputs metadata alongside criteria.

## Standard Stack

No new libraries required. Phase 4 builds entirely on Phase 1-3 infrastructure.

### Existing Stack (Reused)
| Component | Version | Purpose | Phase 4 Usage |
|-----------|---------|---------|---------------|
| Claude API (anthropic) | 0.40+ | AI analysis | Extend criteria generation prompt to also classify sources |
| Pydantic v2 | 2.x | Model validation | New `SourceMetadata` model, extend `ComparisonResult` |
| FastAPI | 0.128+ | API routing | New PATCH flag endpoint |
| TanStack Query v5 | 5.x | Async state | Mutation for flag toggle with optimistic update |
| Tailwind CSS v4 | 4.x | Styling | Badge and icon styles matching existing patterns |

### No New Dependencies
```bash
# No new packages needed
```

## Architecture Patterns

### Data Model Extension

The key architectural decision: where to store source metadata.

**Option A (chosen): `source_metadata` dict on `ComparisonResult` keyed by URL**
```python
# models.py additions
from typing import Literal

class SourceMetadata(BaseModel):
    """Metadata for a single source URL."""
    quality: Literal["peer-reviewed", "government", "industry", "news", "blog", "unknown"] = "unknown"
    flagged: bool = False
    last_verified: datetime | None = None  # Set to comparison created_at time

class ComparisonResult(BaseModel):
    # ... existing fields unchanged ...
    source_metadata: dict[str, SourceMetadata] = {}  # keyed by URL
```

**Why this approach (not embedding in Criterion.sources):**
- `Criterion.sources: list[str]` stays unchanged - no migration needed for existing JSON files
- Multiple criteria can cite the same source; metadata lives once, not duplicated
- Flag endpoint can address a single URL globally across all criteria
- Frontend can look up `source_metadata[url]` by URL when rendering

**Backward compatibility:** `source_metadata: dict[str, SourceMetadata] = {}` defaults to empty dict. All existing stored JSON files load correctly without migration.

### Recommended Project Structure Additions
```
backend/app/
├── models.py           # EXTEND: Add SourceMetadata, add source_metadata field to ComparisonResult
├── services/
│   └── claude_service.py  # EXTEND: Add source classification to generate_criteria prompt
└── routers/
    └── comparison.py   # EXTEND: Add PATCH /api/comparisons/{id}/sources/{url}/flag

frontend/src/features/
├── results/
│   └── ScoringExplainer.tsx  # EXTEND: Add confidence badge explanation
└── criteria/
    └── CriteriaEditor.tsx    # EXTEND: Enhanced source display with badges + flag icons
```

### Pattern 1: Claude Source Classification in Existing Prompt

**What:** Extend `generate_criteria` in `claude_service.py` to also output source quality classifications
**When to use:** During the initial comparison generation (no extra API call)
**How:** Add `source_classifications` to the JSON schema Claude must return

```python
# Extended CriteriaOutput in claude_service.py
class SourceClassification(BaseModel):
    """AI classification of a single source."""
    url: str
    quality: Literal["peer-reviewed", "government", "industry", "news", "blog", "unknown"]
    last_verified: str  # ISO date string - use the date from the source if available

class CriteriaOutput(BaseModel):
    """Full criteria generation output - extended for Phase 4."""
    criteria: list[CriterionOutput] = Field(min_length=3, max_length=5)
    winner: str
    reasoning: str
    source_classifications: list[SourceClassification] = Field(default_factory=list)
```

**Prompt addition** (append to existing prompt in `generate_criteria`):

```python
# Add to the existing prompt string in claude_service.py
classification_section = """
6. For each source URL you cite, also classify it in the source_classifications array:
   - "peer-reviewed": Academic journals, research papers, university publications
   - "government": .gov domains, official government reports, regulatory agencies
   - "industry": Trade associations, corporate research, industry bodies
   - "news": News outlets, journalism, media coverage
   - "blog": Personal blogs, opinion pieces, informal posts
   - "unknown": Cannot determine from URL/content

   Also estimate the last_verified date from the source content if visible, otherwise use today's date.
"""
```

**Updated JSON format instruction** (replace in existing prompt):

```python
# Updated format section in the prompt
"""RESPOND WITH ONLY A JSON OBJECT in this exact format:
{
  "criteria": [
    {
      "name": "Criterion Name",
      "description": "Why this matters",
      "score_a": 75,
      "score_b": 60,
      "weight": 30,
      "sources": ["https://example.com/source"]
    }
  ],
  "winner": "a",
  "reasoning": "2-3 sentence explanation",
  "source_classifications": [
    {
      "url": "https://example.com/source",
      "quality": "government",
      "last_verified": "2025-01-15"
    }
  ]
}"""
```

**In orchestrator.py** - convert classifications to `source_metadata` on the result:

```python
# In generate_comparison, after generate_criteria returns:
from datetime import datetime

source_metadata = {}
for sc in criteria_output.source_classifications:
    source_metadata[sc.url] = SourceMetadata(
        quality=sc.quality,
        flagged=False,
        last_verified=datetime.fromisoformat(sc.last_verified) if sc.last_verified else datetime.now(),
    )

result = ComparisonResult(
    # ... existing fields ...
    source_metadata=source_metadata,
)
```

### Pattern 2: Confidence Score Calculation (Server-Side)

**What:** Compute High/Medium/Low confidence per criterion from source quality + count
**When to use:** Display confidence badge next to each criterion name
**Where:** In orchestrator or as a property computed from existing data

```python
# Pure function - no AI call needed
def compute_confidence(
    sources: list[str],
    source_metadata: dict[str, "SourceMetadata"]
) -> Literal["high", "medium", "low"]:
    """
    Compute confidence from source quality and count.

    Rules:
    - high: 2+ sources AND at least one peer-reviewed or government source
    - medium: 2+ sources OR 1 source of high quality (peer-reviewed/government)
    - low: 1 source of non-high quality, or no sources
    """
    if not sources:
        return "low"

    metas = [source_metadata.get(url) for url in sources if url in source_metadata]
    high_quality = {"peer-reviewed", "government"}

    has_high_quality = any(m.quality in high_quality for m in metas if m)
    source_count = len(sources)

    if source_count >= 2 and has_high_quality:
        return "high"
    elif source_count >= 2 or has_high_quality:
        return "medium"
    else:
        return "low"
```

**Store confidence on Criterion** (add to model):

```python
class Criterion(BaseModel):
    # ... existing fields ...
    confidence: Literal["high", "medium", "low"] = "low"  # NEW
```

Confidence is computed once in orchestrator when building criteria and stored. It does not need to update dynamically (flagging sources does not recompute confidence - that would be overcomplicated).

### Pattern 3: Flag Endpoint

**What:** PATCH endpoint to toggle flagged state of a source
**When to use:** User clicks flag icon in `CriteriaEditor`

```python
# In routers/comparison.py

class SourceFlagUpdate(BaseModel):
    flagged: bool

@router.patch("/api/comparisons/{comparison_id}/sources/flag")
async def flag_source(comparison_id: str, data: SourceFlagUpdate, url: str):
    """Toggle flagged state of a source URL."""
    result = storage.read_result(comparison_id)
    if not result:
        raise HTTPException(status_code=404, detail="Comparison not found")

    # Get or create metadata entry
    if url not in result.source_metadata:
        result.source_metadata[url] = SourceMetadata(flagged=data.flagged)
    else:
        result.source_metadata[url].flagged = data.flagged

    storage.write_result(comparison_id, result)
    return {"url": url, "flagged": data.flagged}
```

**Alternative endpoint shape** (simpler, avoids query params):

```python
@router.patch("/api/comparisons/{comparison_id}/sources/flag")
async def flag_source(comparison_id: str, body: dict):
    url = body["url"]
    flagged = body["flagged"]
    # ...
```

Use the body approach to avoid URL encoding issues with source URLs as path/query params.

### Pattern 4: Source Display in CriteriaEditor (Frontend)

**What:** Enhanced source row with quality badge, domain name, flag icon
**When to use:** Replace the existing `[1] [2] [3]` numeric links in `CriteriaEditor`
**Current code (lines 141-157 in CriteriaEditor.tsx):**

```tsx
{criterion.sources.length > 0 && (
  <div className="mt-2 pt-2 border-t border-gray-100">
    <span className="text-xs text-gray-500">Sources: </span>
    {criterion.sources.map((src, i) => (
      <a key={i} href={src} target="_blank" rel="noopener noreferrer"
         className="text-xs text-blue-600 hover:underline ml-1"
         onClick={(e) => e.stopPropagation()}>
        [{i + 1}]
      </a>
    ))}
  </div>
)}
```

**Replacement pattern:**

```tsx
// New SourceLink component (small, inline)
interface SourceLinkProps {
  url: string
  metadata?: SourceMetadata
  comparisonId: string
  onFlagToggle: (url: string, flagged: boolean) => void
}

function SourceLink({ url, metadata, comparisonId, onFlagToggle }: SourceLinkProps) {
  const domain = new URL(url).hostname.replace('www.', '')
  const flagged = metadata?.flagged ?? false

  const qualityBadge = metadata?.quality ? QUALITY_BADGE_MAP[metadata.quality] : null

  return (
    <span className={`inline-flex items-center gap-1 mr-2 ${flagged ? 'opacity-50 line-through' : ''}`}>
      {qualityBadge && (
        <span className={`px-1 py-0.5 text-xs rounded ${qualityBadge.classes}`}>
          {qualityBadge.label}
        </span>
      )}
      <a href={url} target="_blank" rel="noopener noreferrer"
         className="text-xs text-blue-600 hover:underline"
         onClick={(e) => e.stopPropagation()}>
        {domain}
      </a>
      <button
        onClick={(e) => { e.stopPropagation(); onFlagToggle(url, !flagged) }}
        className={`text-xs ${flagged ? 'text-red-500' : 'text-gray-300 hover:text-gray-500'}`}
        title={flagged ? 'Remove flag' : 'Flag as unreliable'}
      >
        ⚑
      </button>
    </span>
  )
}

const QUALITY_BADGE_MAP = {
  'peer-reviewed': { label: 'Peer', classes: 'bg-green-100 text-green-700' },
  'government':    { label: 'Gov',  classes: 'bg-blue-100 text-blue-700' },
  'industry':      { label: 'Ind',  classes: 'bg-purple-100 text-purple-700' },
  'news':          { label: 'News', classes: 'bg-gray-100 text-gray-600' },
  'blog':          { label: 'Blog', classes: 'bg-yellow-100 text-yellow-700' },
  'unknown':       { label: null,   classes: '' },  // No badge for unknown
}
```

### Pattern 5: Confidence Badge on Criterion (Frontend)

**What:** High/Medium/Low badge next to criterion name, consistent with existing "High Impact" / "Medium Impact" badges
**Current badge pattern** (from CriteriaEditor.tsx lines 91-99):

```tsx
// EXISTING - sensitivity badge pattern (to match)
const sensitivityBadge = sensitivity > 0.7 ? (
  <span className="inline-block px-2 py-0.5 text-xs font-medium bg-red-100 text-red-700 rounded">
    High Impact
  </span>
) : sensitivity > 0.4 ? (
  <span className="inline-block px-2 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-700 rounded">
    Medium Impact
  </span>
) : null
```

**New confidence badge** (same pattern):

```tsx
// Match exact same className structure
const confidenceBadge = criterion.confidence === 'high' ? (
  <span className="inline-block px-2 py-0.5 text-xs font-medium bg-green-100 text-green-700 rounded">
    High Confidence
  </span>
) : criterion.confidence === 'medium' ? (
  <span className="inline-block px-2 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-700 rounded">
    Med Confidence
  </span>
) : (
  <span className="inline-block px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-600 rounded">
    Low Confidence
  </span>
)
```

Place this badge in the existing badge group alongside the sensitivity badge and custom badge (lines 108-119 of CriteriaEditor.tsx).

### Pattern 6: Flag Toggle Mutation (Frontend)

**What:** TanStack Query mutation for flag toggle with optimistic update
**When to use:** User clicks flag icon on a source

```typescript
// In CriteriaEditor or a custom hook
const flagMutation = useMutation({
  mutationFn: async ({ url, flagged }: { url: string; flagged: boolean }) => {
    const res = await fetch(
      `${API_BASE}/api/comparisons/${comparisonId}/sources/flag`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, flagged }),
      }
    )
    if (!res.ok) throw new Error('Flag update failed')
    return res.json()
  },
  onMutate: async ({ url, flagged }) => {
    await queryClient.cancelQueries({ queryKey: ['comparison', comparisonId] })
    const previous = queryClient.getQueryData(['comparison', comparisonId])

    queryClient.setQueryData(['comparison', comparisonId], (old: any) => {
      if (!old) return old
      return {
        ...old,
        source_metadata: {
          ...old.source_metadata,
          [url]: { ...(old.source_metadata?.[url] ?? {}), flagged },
        }
      }
    })

    return { previous }
  },
  onError: (_err, _vars, context) => {
    queryClient.setQueryData(['comparison', comparisonId], context?.previous)
  },
  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: ['comparison', comparisonId] })
  },
})
```

### Anti-Patterns to Avoid

- **Domain-based heuristics for quality:** User decision is AI classification - do not add a parallel heuristic classifier. Claude's classification during generation is the sole source of quality data.
- **Separate API call to classify sources:** Classify sources in the same `generate_criteria` call. No second Claude call needed.
- **Embedding metadata in `Criterion.sources`:** Keep `sources: list[str]` as-is. Use `source_metadata` dict on `ComparisonResult`. Avoids breaking existing stored JSON.
- **Recomputing confidence when sources are flagged:** Confidence is fixed at generation time. Flagging is a user annotation, not a quality signal that changes the score. Keep them separate.
- **Storing last_verified as a string in the model:** Use `datetime | None` in Pydantic; let Pydantic handle serialization. The Claude prompt asks for ISO date strings which Pydantic can parse.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Source URL encoding in endpoint | Custom encoding/decoding | Pass URL in request body as JSON field | Avoids double-encoding issues |
| Quality tier labels in frontend | Hardcoded string checks | `QUALITY_BADGE_MAP` lookup object | Single source of truth for labels + styles |
| Optimistic flag toggle | Manual state management | TanStack Query `onMutate` + rollback | Same pattern already used in CriteriaEditor for criterion updates |
| Confidence calculation | Complex algorithm | Simple rule-based function (2+ sources + high-quality = high) | Transparent, explainable to users |
| Domain name from URL | Regex | `new URL(url).hostname.replace('www.', '')` | Native browser API, handles edge cases |

## Common Pitfalls

### Pitfall 1: Claude Omits source_classifications

**What goes wrong:** Claude generates criteria correctly but returns empty `source_classifications` array
**Why it happens:** It's at the end of a long JSON response and Claude deprioritizes it
**How to avoid:**
- Put source_classifications instruction BEFORE the criteria format in the prompt
- Add explicit reminder: "You MUST include source_classifications for every URL you use in sources arrays"
- Validate after parsing: if `source_classifications` is empty but criteria have sources, log a warning and create `unknown` entries for each cited URL
**Fallback code:**
```python
# After parsing CriteriaOutput, ensure all cited URLs have metadata
all_cited_urls = {url for c in criteria_output.criteria for url in c.sources}
for url in all_cited_urls:
    if not any(sc.url == url for sc in criteria_output.source_classifications):
        criteria_output.source_classifications.append(
            SourceClassification(url=url, quality="unknown", last_verified=datetime.now().isoformat())
        )
```
**Warning signs:** All sources show "unknown" quality after generation

### Pitfall 2: Backward Compatibility Break on Old JSON Files

**What goes wrong:** Loading old comparison results (from Phase 1-3) fails with Pydantic validation error
**Why it happens:** `source_metadata` field added to `ComparisonResult` without default
**How to avoid:**
- Always set `source_metadata: dict[str, SourceMetadata] = {}` with default empty dict
- Same for `confidence: Literal["high", "medium", "low"] = "low"` on `Criterion`
- Test by loading an existing JSON file after model changes
**Warning signs:** `storage.read_result()` raises validation error on old comparisons

### Pitfall 3: Flag State Lost on TanStack Query Cache Invalidation

**What goes wrong:** User flags a source, optimistic update shows it flagged, then cache refresh resets it
**Why it happens:** `invalidateQueries` triggers a refetch that may return stale data before write completes
**How to avoid:**
- The `onSettled` refetch is correct - the server should have the updated value by then
- Use `staleTime: 0` for comparison data so refetch always hits server
- If timing issues arise, add a short delay before invalidation
**Warning signs:** Flag icon flickers on/off after clicking

### Pitfall 4: URL Special Characters Break Flag Endpoint

**What goes wrong:** Source URLs with `?`, `&`, `#` cause routing or parsing issues
**Why it happens:** If URL is a path/query param, special characters need encoding
**How to avoid:**
- Pass URL in request body as JSON (not as path parameter or query string)
- `PATCH /api/comparisons/{id}/sources/flag` with `{ "url": "...", "flagged": true }` in body
**Warning signs:** 404 or 422 errors when flagging sources with query strings in their URLs

### Pitfall 5: Confidence Badge Always Shows "Low" for Existing Comparisons

**What goes wrong:** Old comparisons (loaded from disk) show Low Confidence on all criteria
**Why it happens:** Pre-Phase-4 comparisons don't have source_metadata so confidence defaults to "low"
**How to avoid:**
- This is acceptable behavior - old comparisons genuinely lack quality metadata
- Display "No quality data" or omit badge entirely if `source_metadata` is empty
- Add a note in the UI: "Re-run comparison to see confidence signals"
**Warning signs:** Users confused why confidence shows on new comparisons but not old ones

## Code Examples

### SourceMetadata Pydantic Model

```python
# backend/app/models.py additions
from typing import Literal
from datetime import datetime

class SourceMetadata(BaseModel):
    """Quality and trust metadata for a single source URL."""
    quality: Literal["peer-reviewed", "government", "industry", "news", "blog", "unknown"] = "unknown"
    flagged: bool = False
    last_verified: datetime | None = None
```

### Extended ComparisonResult

```python
class ComparisonResult(BaseModel):
    comparison_id: str
    status: Literal["processing", "completed", "error"]
    option_a_name: str
    option_b_name: str
    intent: str
    criteria: list[Criterion] = []
    winner: Literal["a", "b", "tie"] | None = None
    reasoning: str = ""
    created_at: datetime
    completed_at: datetime | None = None
    research_a: dict | None = None
    research_b: dict | None = None
    source_metadata: dict[str, SourceMetadata] = {}  # NEW: keyed by URL
```

### Extended Criterion Model

```python
class Criterion(BaseModel):
    id: str
    name: str
    description: str
    score_a: float = Field(ge=0, le=100)
    score_b: float = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=100, default=50)
    sources: list[str] = []
    origin: Literal["ai", "user"] = "ai"
    confidence: Literal["high", "medium", "low"] = "low"  # NEW
```

### Updated Frontend Types

```typescript
// frontend/src/features/comparison/types.ts additions

export type SourceQuality = 'peer-reviewed' | 'government' | 'industry' | 'news' | 'blog' | 'unknown'
export type ConfidenceLevel = 'high' | 'medium' | 'low'

export interface SourceMetadata {
  quality: SourceQuality
  flagged: boolean
  last_verified: string | null  // ISO datetime string
}

export interface Criterion {
  id: string
  name: string
  description: string
  score_a: number
  score_b: number
  weight: number
  sources: string[]
  origin: 'ai' | 'user'
  confidence: ConfidenceLevel  // NEW
}

export interface ComparisonResult {
  // ... existing fields ...
  source_metadata: Record<string, SourceMetadata>  // NEW
}
```

### Claude Prompt Extension (Key Section)

```python
# Addition to the CRITICAL RULES in generate_criteria prompt (claude_service.py)
# Insert as rule 6, BEFORE the JSON format specification

"""6. For each source URL cited in criteria, classify it in source_classifications:
   Types: peer-reviewed, government, industry, news, blog, unknown
   - peer-reviewed: academic journals, research papers, .edu publications
   - government: .gov, official agencies, regulatory bodies
   - industry: trade associations, corporate research, .org industry groups
   - news: news outlets, media, journalism
   - blog: personal blogs, Medium posts, informal commentary
   - unknown: cannot determine from content

   Include last_verified as ISO date (YYYY-MM-DD) from source, or today if unknown.

   You MUST classify every URL that appears in any criterion's sources array."""
```

### Confidence Calculation Function

```python
# backend/app/services/orchestrator.py or models.py
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .models import SourceMetadata

def compute_confidence(
    sources: list[str],
    source_metadata: dict[str, "SourceMetadata"]
) -> str:
    """Compute High/Medium/Low confidence from source quality and count."""
    if not sources:
        return "low"

    HIGH_QUALITY = {"peer-reviewed", "government"}
    metas = [source_metadata[url] for url in sources if url in source_metadata]
    has_high_quality = any(m.quality in HIGH_QUALITY for m in metas)
    count = len(sources)

    if count >= 2 and has_high_quality:
        return "high"
    elif count >= 2 or has_high_quality:
        return "medium"
    else:
        return "low"
```

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Domain heuristics (.gov = government) | AI classifies based on content analysis | More accurate, no hard-coded rule maintenance |
| Sources shown as [1][2][3] numeric refs | Domain names with quality badges | Users see where claims come from at a glance |
| No way to mark bad sources | Flag toggle persisted to JSON | User trust layer without requiring moderation |
| All claims treated with equal confidence | High/Med/Low badges per criterion | Users can weight their own trust accordingly |

**Not yet in scope (Phase 5 or later):**
- Automatic re-classification on flag (flagging does not recompute confidence)
- Source freshness alerts (e.g., "source is 3 years old")
- Cross-comparison source reputation tracking

## Open Questions

1. **Where to call `compute_confidence`**
   - What we know: Confidence must be stored on `Criterion` (not computed client-side) so it persists
   - What's unclear: Whether to call in `orchestrator.py` after generation, or as a Pydantic validator
   - Recommendation: Call in `orchestrator.py` when building the `Criterion` list, immediately after converting `CriteriaOutput`. Simple and explicit.

2. **Flag endpoint URL encoding**
   - What we know: Source URLs often contain query strings and special characters
   - Recommendation: Accept URL in JSON request body, not as a path/query parameter

3. **Confidence for user-added criteria**
   - What we know: User-added criteria have `sources: []` by default, so confidence = "low"
   - Recommendation: Omit the confidence badge entirely for `origin: "user"` criteria - they don't have AI-sourced claims to assess confidence on

4. **"Last verified" display format**
   - What we know: Success criteria require showing this timestamp
   - Recommendation: Show as tooltip on hover over the source domain link (e.g., "Last verified: Jan 15, 2025") to keep the inline display clean

## Sources

### Primary (HIGH confidence)
- Existing codebase analysis: `backend/app/models.py`, `backend/app/services/claude_service.py`, `backend/app/services/orchestrator.py`, `frontend/src/features/criteria/CriteriaEditor.tsx`, `frontend/src/features/comparison/types.ts`
- TanStack Query v5 optimistic updates pattern - already verified and working in `CriteriaEditor.tsx` (Phase 3)
- Pydantic v2 `model_dump(mode='json')` and `model_validate()` - already in use in `storage.py`
- FastAPI PATCH pattern with `exclude_unset=True` - already in use in `comparison.py`

### Secondary (MEDIUM confidence)
- Phase 3 RESEARCH.md patterns (all verified working after Phase 3 execution)
- Existing badge pattern in `CriteriaEditor.tsx` (sensitivity badges) - directly reusable

### Tertiary (LOW confidence)
- Claude source classification prompt effectiveness - will need validation during execution; fallback to "unknown" if Claude omits classifications

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new libraries, all existing
- Data model extension: HIGH - Straightforward Pydantic model addition with backward-compatible defaults
- Claude prompt extension: MEDIUM - Prompt engineering effectiveness requires empirical validation; fallback handling covers failure case
- Frontend badge UI: HIGH - Directly mirrors existing sensitivity badge pattern
- Flag endpoint: HIGH - Standard PATCH pattern already used in codebase

**Research date:** 2026-02-10
**Valid until:** 2026-03-10 (30 days - stable patterns, no fast-moving dependencies)
