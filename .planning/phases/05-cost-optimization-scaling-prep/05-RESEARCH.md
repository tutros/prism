# Phase 5: Cost Optimization + Scaling Prep - Research

**Researched:** 2026-02-12
**Domain:** API cost monitoring, caching strategy, spending controls, token usage tracking
**Confidence:** HIGH

---

## Summary

Phase 5 implements infrastructure improvements that surface API cost visibility, prevent runaway spending, and cache Tavily/Claude results to reduce duplicate API calls. The user-facing changes are minimal (cache age indicators + "Refresh" option); the developer-facing changes are the primary deliverables (monitoring dashboard, daily spending caps, token usage breakdown).

The codebase already has prompt caching partially implemented (`cache_control: ephemeral` on the system prompt in three Claude service files). The key work in this phase is: (1) capturing and persisting the usage fields already returned by the API, (2) adding a Tavily result cache with 24h TTL using a simple in-memory dict, (3) adding a comparison result cache, (4) building a developer monitoring endpoint to aggregate token/cost metrics, and (5) adding a daily spending cap enforced server-side.

**Primary recommendation:** Use the `response.usage` fields already returned by the Anthropic SDK to track token consumption. Store metrics in a JSON file alongside existing comparison results (same atomic-write pattern). Implement Tavily caching as a simple in-memory `dict` with timestamps — no external dependencies needed for this single-server dev tool.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| anthropic | >=0.40.0 (already installed) | Token usage via `response.usage` | Already in use; `usage` object contains all cache fields |
| cachetools | 5.x | TTL dict for Tavily result cache | Pure Python, zero deps, battle-tested; provides `TTLCache` class |
| Python stdlib | 3.11+ | `datetime`, `json`, `os` for spending cap storage | No new deps needed |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| cachetools | 5.5.x | `TTLCache(maxsize=N, ttl=86400)` for 24h Tavily cache | Preferred over hand-rolling TTL dict logic |

**Note on cachetools:** The existing codebase already avoids external caching dependencies (Redis, Memcached). `cachetools` is a lightweight, widely-used stdlib-compatible library that provides exactly the `TTLCache` needed. It is not in the current `requirements.txt` but is a single-line addition. Alternatively, a hand-rolled `dict` with `(result, timestamp)` tuples works for this scale.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| cachetools TTLCache | Plain dict + timestamp check | Equivalent for single-worker; TTLCache auto-evicts; either works |
| cachetools TTLCache | Redis | Redis is overkill for a dev tool with a single Uvicorn worker |
| JSON file for metrics | SQLite | SQLite adds a dep; JSON + atomic writes matches existing storage.py pattern |

### Installation

```bash
pip install cachetools
```

---

## Architecture Patterns

### Recommended Project Structure

New files to add (minimal footprint):

```
backend/app/
├── services/
│   ├── usage_tracker.py      # Token usage accumulation + cost calculation
│   ├── tavily_cache.py       # TTLCache wrapper for Tavily results (24h)
│   └── spending_guard.py     # Daily spending cap enforcement
├── routers/
│   └── monitoring.py         # GET /api/monitoring - developer dashboard
└── data/
    └── usage_metrics.json    # Persisted token/cost metrics (atomic write)
```

Existing files to modify minimally:

```
backend/app/services/claude_service.py     # Extract usage fields from response
backend/app/services/criteria_service.py  # Extract usage fields from response
backend/app/services/flip_service.py      # Extract usage fields from response
backend/app/services/tavily_service.py    # Check cache before calling Tavily
backend/app/services/orchestrator.py      # Pass usage up; check spending cap
backend/app/models.py                     # Add cache_age field to ComparisonResult
```

### Pattern 1: Capture Usage From Anthropic Response

**What:** Extract `response.usage` fields after every `client.messages.create()` call.

**When to use:** Every Claude API call in `claude_service.py`, `criteria_service.py`, `flip_service.py`.

**Example:**

```python
# Source: https://platform.claude.com/docs/en/docs/build-with-claude/prompt-caching
response = await client.messages.create(
    model="claude-sonnet-4-5-20250929",
    ...
)

# usage fields available on every response:
usage = response.usage
# usage.input_tokens             - tokens AFTER last cache breakpoint (not cached)
# usage.output_tokens            - output tokens
# usage.cache_creation_input_tokens  - tokens written to cache (1.25x price)
# usage.cache_read_input_tokens      - tokens read from cache (0.1x price)

total_input = (
    (usage.cache_read_input_tokens or 0)
    + (usage.cache_creation_input_tokens or 0)
    + usage.input_tokens
)
```

**Important:** `input_tokens` is only tokens AFTER the last cache breakpoint. Total input = `cache_read + cache_creation + input_tokens`.

### Pattern 2: Cost Calculation

Sonnet 4.5 pricing (confirmed from official docs, 2026):
- Base input: $3.00 / MTok
- Cache write (5m): $3.75 / MTok (1.25x base)
- Cache read: $0.30 / MTok (0.1x base)
- Output: $15.00 / MTok

```python
# Source: https://platform.claude.com/docs/en/about-claude/pricing
PRICE_PER_TOKEN = {
    "claude-sonnet-4-5-20250929": {
        "input": 3.00 / 1_000_000,
        "cache_write": 3.75 / 1_000_000,
        "cache_read": 0.30 / 1_000_000,
        "output": 15.00 / 1_000_000,
    }
}

def calculate_cost(model: str, usage) -> float:
    prices = PRICE_PER_TOKEN.get(model, PRICE_PER_TOKEN["claude-sonnet-4-5-20250929"])
    return (
        (usage.input_tokens * prices["input"])
        + ((usage.cache_creation_input_tokens or 0) * prices["cache_write"])
        + ((usage.cache_read_input_tokens or 0) * prices["cache_read"])
        + (usage.output_tokens * prices["output"])
    )
```

### Pattern 3: Tavily Result Cache (24h TTL)

**What:** Cache Tavily search results by query string. Same query within 24h returns cached result.

**When to use:** Before every `tavily.search()` call in `tavily_service.py`.

```python
# Using cachetools (recommended)
from cachetools import TTLCache
import asyncio

_TAVILY_CACHE: TTLCache = TTLCache(maxsize=200, ttl=86400)  # 24h TTL
_CACHE_LOCK = asyncio.Lock()

async def search_option(option: str) -> OptionResearch:
    query = f"{option} hidden costs environmental impact subsidies externalities supply chain"
    cache_key = query.lower().strip()

    async with _CACHE_LOCK:
        if cache_key in _TAVILY_CACHE:
            cached = _TAVILY_CACHE[cache_key]
            return OptionResearch(
                option=option,
                results=cached["results"],
                cached_at=cached["cached_at"],  # for cache age indicator
            )

    # Cache miss - call Tavily
    result = await _do_tavily_search(query)

    async with _CACHE_LOCK:
        _TAVILY_CACHE[cache_key] = {
            "results": result.results,
            "cached_at": datetime.utcnow().isoformat(),
        }

    return result
```

**Alternative without cachetools (hand-rolled):**

```python
_TAVILY_CACHE: dict[str, dict] = {}
_CACHE_TTL_SECONDS = 86400

def _is_expired(cached_at: str) -> bool:
    age = datetime.utcnow() - datetime.fromisoformat(cached_at)
    return age.total_seconds() > _CACHE_TTL_SECONDS
```

### Pattern 4: Daily Spending Cap

**What:** In-memory accumulator of today's cost. Raise HTTP 429 if cap exceeded.

**When to use:** At the start of `generate_comparison()` in `orchestrator.py`.

```python
# spending_guard.py
from datetime import date
import threading

_today = date.today().isoformat()
_daily_cost_usd: float = 0.0
_lock = threading.Lock()
_DAILY_CAP_USD = float(os.environ.get("DAILY_SPEND_CAP_USD", "5.0"))

def check_and_add_cost(cost: float) -> None:
    """Add cost to daily total. Raises ValueError if cap exceeded."""
    global _today, _daily_cost_usd
    with _lock:
        today = date.today().isoformat()
        if today != _today:
            _today = today
            _daily_cost_usd = 0.0  # reset on new day
        if _daily_cost_usd + cost > _DAILY_CAP_USD:
            raise ValueError(
                f"Daily spending cap of ${_DAILY_CAP_USD:.2f} exceeded. "
                f"Current: ${_daily_cost_usd:.2f}"
            )
        _daily_cost_usd += cost
```

**Note:** This is in-memory only and resets on restart. For a dev tool, this is acceptable. Pre-flight check using average cost per comparison (~$0.02) before calling APIs is sufficient.

### Pattern 5: Monitoring Endpoint

**What:** `GET /api/monitoring` returns aggregated token usage and cost breakdown.

```python
# monitoring.py
@router.get("/api/monitoring")
async def get_monitoring():
    return {
        "today": {
            "cost_usd": daily_cost_usd,
            "cap_usd": DAILY_CAP_USD,
            "comparisons_run": comparison_count,
        },
        "all_time": {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cache_read_tokens": total_cache_read,
            "total_cache_creation_tokens": total_cache_write,
            "total_cost_usd": total_cost,
            "estimated_savings_usd": savings,  # cost delta from cache reads
        },
        "cache_stats": {
            "tavily_entries": len(_TAVILY_CACHE),
            "tavily_hit_rate": hit_rate,
        }
    }
```

### Pattern 6: Cache Age Indicator on ComparisonResult

**What:** Store `tavily_cached_at` timestamp on comparison results to drive frontend "Refresh" UI.

Add to `models.py`:
```python
class ComparisonResult(BaseModel):
    ...
    tavily_cached_at: datetime | None = None  # None = fresh search
```

Frontend shows "Results from cached data (Xh ago)" when `tavily_cached_at` is set.

### Anti-Patterns to Avoid

- **Storing full Tavily responses in Redis:** Overkill for single-server dev tool; in-memory TTLCache is sufficient.
- **Making token tracking synchronous/blocking:** Use `asyncio.Lock` for cache; `threading.Lock` only for the spending guard (called from sync context).
- **Hand-rolling cost calc with wrong token counts:** Always compute `total_input = cache_read + cache_creation + input_tokens`. Using `input_tokens` alone underestimates cost when caching is active.
- **Assuming `cache_creation_input_tokens` is always populated:** It can be `None` or `0`; use `or 0` guards.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TTL cache eviction | Custom `dict` with manual cleanup loops | `cachetools.TTLCache` | Auto-evicts on access; handles max size; thread-safe-ish |
| Token cost calculation | Custom pricing table fetched from API | Hard-coded `PRICE_PER_TOKEN` dict | Pricing rarely changes; API doesn't expose pricing endpoint |
| Atomic JSON writes | `open(file, 'w')` directly | Existing `storage.py` `write_result` pattern | Already implemented; prevents corruption on crash |

**Key insight:** The Anthropic SDK already returns all the data needed. The main work is capturing `response.usage` in the three service files and routing it to a persistent counter.

---

## Common Pitfalls

### Pitfall 1: Wrong Total Input Token Count

**What goes wrong:** Using `usage.input_tokens` directly as "total input" produces a much lower count than reality when prompt caching is active.

**Why it happens:** `input_tokens` only represents tokens AFTER the last cache breakpoint (the user message portion, typically 50-200 tokens). The 1000+ token system prompt is in `cache_creation_input_tokens` or `cache_read_input_tokens`.

**How to avoid:** Always compute:
```python
total_input = usage.input_tokens + (usage.cache_creation_input_tokens or 0) + (usage.cache_read_input_tokens or 0)
```

**Warning signs:** Total cost per comparison seems unrealistically low (< $0.001).

### Pitfall 2: Cache Miss on System Prompt - 5-Minute TTL

**What goes wrong:** The system prompt cache expires every 5 minutes of inactivity. If no comparison runs for 5 minutes, the next call is a cache write (1.25x cost), not a cache read.

**Why it happens:** `cache_control: ephemeral` defaults to 5-minute TTL.

**How to avoid:** This is expected behavior; log `cache_creation_input_tokens > 0` as a "cache miss" event in monitoring. The 5-minute TTL is acceptable for an interactive tool. No code change needed.

**Warning signs:** `cache_creation_input_tokens` is always non-zero (cache never hits).

### Pitfall 3: Tavily Cache Key Collisions

**What goes wrong:** Two semantically different queries hash to the same key; one gets the other's results.

**Why it happens:** Using too-simple cache keys like just `option` rather than the full query string.

**How to avoid:** Use the full query string including the suffix ("hidden costs environmental impact...") as the cache key. The query string is deterministic per `option` value.

### Pitfall 4: asyncio.Lock vs threading.Lock Confusion

**What goes wrong:** Using `threading.Lock` inside an async function causes deadlocks; using `asyncio.Lock` outside async context raises errors.

**Why it happens:** FastAPI mixes sync and async contexts (background tasks use asyncio; route handlers are async).

**How to avoid:**
- Tavily cache: `asyncio.Lock` (called from async `search_option`)
- Spending guard: `threading.Lock` is fine (stateless mutation, very fast, no await inside)

### Pitfall 5: Spending Cap Reset on Restart

**What goes wrong:** In-memory daily cost counter resets to 0 on server restart, allowing more than the daily cap if server restarts frequently.

**Why it happens:** Cap state is in-memory only.

**How to avoid:** For a dev tool, this is acceptable. Document the limitation. Could persist to `data/daily_spend.json` if needed (same atomic pattern). This phase's success criteria doesn't require persistence across restarts.

### Pitfall 6: Comparison Result Cache vs Tavily Cache

**What goes wrong:** Confusing what to cache. The phase description mentions "comparison result caching (1-7 day TTL)" separately from Tavily caching.

**Why it happens:** Ambiguous requirement.

**Clarification:** The existing `JSONStorage` already persists comparison results indefinitely. The "comparison result cache" described in the phase is the existing JSON storage — results are already cached. The new work is:
1. Tavily search cache (24h TTL, avoids re-searching the web for identical options)
2. Cache age indicators (surface to user when Tavily data is from cache vs fresh)

No new "comparison result cache" is needed beyond what exists.

---

## Code Examples

Verified patterns from official sources:

### Accessing Usage Fields After a Request

```python
# Source: https://platform.claude.com/docs/en/docs/build-with-claude/prompt-caching
response = await client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    system=[
        {"type": "text", "text": "..."},
        {"type": "text", "text": "...", "cache_control": {"type": "ephemeral"}},
    ],
    messages=[{"role": "user", "content": user_prompt}],
)

# All usage fields:
print(response.usage.input_tokens)                    # after-breakpoint tokens
print(response.usage.output_tokens)                   # output tokens
print(response.usage.cache_creation_input_tokens)     # tokens written to cache
print(response.usage.cache_read_input_tokens)         # tokens read from cache

# First call example JSON: {"cache_creation_input_tokens":188086,"cache_read_input_tokens":0,"input_tokens":21,"output_tokens":393}
# Second call example JSON: {"cache_creation_input_tokens":0,"cache_read_input_tokens":188086,"input_tokens":21,"output_tokens":393}
```

### TTLCache with cachetools

```python
# Source: cachetools PyPI / https://cachetools.readthedocs.io/
from cachetools import TTLCache

# 200 entries max, 24h TTL
cache = TTLCache(maxsize=200, ttl=86400)

# Use like a dict; expired entries auto-evict on access
if key in cache:
    return cache[key]
cache[key] = value
```

### Returning Usage From Service Functions

```python
# Pattern: return a UsageRecord alongside the result
from dataclasses import dataclass

@dataclass
class UsageRecord:
    model: str
    input_tokens: int
    output_tokens: int
    cache_creation_tokens: int
    cache_read_tokens: int
    cost_usd: float

async def generate_criteria(...) -> tuple[CriteriaOutput, UsageRecord]:
    response = await client.messages.create(...)
    usage_record = UsageRecord(
        model="claude-sonnet-4-5-20250929",
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        cache_creation_tokens=response.usage.cache_creation_input_tokens or 0,
        cache_read_tokens=response.usage.cache_read_input_tokens or 0,
        cost_usd=calculate_cost("claude-sonnet-4-5-20250929", response.usage),
    )
    ...
    return criteria_output, usage_record
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Prompt caching behind `client.beta.prompt_caching` | GA: standard `client.messages.create()` | Late 2024 | No beta flag needed; remove any `beta.prompt_caching` references |
| `cache_creation_input_tokens` only | `cache_creation` object with per-TTL breakdown (`ephemeral_5m`, `ephemeral_1h`) | 2025 | For 5m-only caching, `cache_creation_input_tokens` is still correct |
| Workspace cache isolation | Starting Feb 5, 2026: workspace-level isolation (was org-level) | Feb 5, 2026 | Affects only multi-workspace orgs; no impact for dev tools |

**Deprecated/outdated:**
- `client.beta.prompt_caching.messages.create()`: Now raises `AttributeError`; use `client.messages.create()` directly.

---

## Open Questions

1. **Model for "lightweight" tasks (flip analysis)**
   - What we know: The phase notes mention "Haiku for lightweight, Sonnet for complex." `flip_service.py` currently uses `claude-sonnet-4-5-20250929` with `max_tokens=1500`.
   - What's unclear: Whether switching `flip_service.py` to Claude Haiku 4.5 ($1/$5 MTok vs $3/$15 MTok) is desirable. Haiku 4.5 is 5x cheaper and within "5 percentage points" of Sonnet on benchmarks.
   - Recommendation: Leave model selection to the planner. The flip analysis produces simple JSON with 2-3 fields; Haiku is likely sufficient. Mark as a planner decision.

2. **Comparison result cache TTL (1-7 day range)**
   - What we know: Phase description says "comparison result caching (1-7 day TTL)" but the existing `JSONStorage` already persists forever.
   - What's unclear: Whether "comparison result caching" means (a) don't re-run AI if same options+intent submitted within 1-7 days, or (b) expire stored JSON results after 7 days.
   - Recommendation: Interpret as (a) — deduplicate identical comparisons by hashing `(option_a, option_b, intent)`. If hash matches a recent result, return the cached comparison ID instead of running the AI pipeline again.

3. **Frontend "Refresh with latest data" interaction**
   - What we know: Success criterion says "User sees cache age indicators and can choose 'Refresh with latest data' for stale results."
   - What's unclear: Does "Refresh" re-run the full comparison (new Tavily + new Claude), or just re-run the Tavily search?
   - Recommendation: "Refresh" should force a new Tavily search (bypass cache) and re-run Claude on the new research. Add a `?force_refresh=true` query param to `POST /api/compare`.

---

## Sources

### Primary (HIGH confidence)

- `/anthropics/anthropic-sdk-python` (Context7) — token counting, usage fields
- `/anthropics/anthropic-cookbook` (Context7) — token monitoring patterns, cache savings calculation
- `https://platform.claude.com/docs/en/docs/build-with-claude/prompt-caching` (Official Anthropic docs) — all cache fields, pricing, TTL, min token requirements, usage field semantics
- `https://platform.claude.com/docs/en/about-claude/pricing` (Official Anthropic docs) — confirmed Sonnet 4.5 / Haiku 4.5 pricing for 2026
- `/tavily-ai/tavily-python` (Context7) — AsyncTavilyClient usage

### Secondary (MEDIUM confidence)

- `https://pypi.org/project/cachetools/` — TTLCache API (verified via multiple sources)
- `https://www.anthropic.com/news/claude-haiku-4-5` (Official Anthropic announcement) — Haiku 4.5 pricing and benchmark comparison

### Tertiary (LOW confidence)

- WebSearch results for FastAPI caching patterns — community patterns only, used for orientation not prescriptive guidance

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — SDK usage fields confirmed via official docs + Context7; pricing confirmed from official pricing page
- Architecture: HIGH — patterns derived from official SDK documentation; follows existing codebase patterns
- Pitfalls: HIGH for items 1-4 (confirmed from official docs); MEDIUM for items 5-6 (design decisions)

**Research date:** 2026-02-12
**Valid until:** 2026-03-12 (30 days; pricing and SDK API are stable)
