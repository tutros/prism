# Prism

An AI-powered decision comparison tool that surfaces hidden costs and systemic impacts invisible in traditional comparisons.

Enter two options and your intent (e.g. "buying a house vs. renting, optimizing for 10-year financial outcome") and the system researches both options via web search, then uses Claude to generate scored criteria covering financial, environmental, social, and long-term factors you might not have considered.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- API keys for [Anthropic](https://console.anthropic.com/settings/keys) and [Tavily](https://app.tavily.com/home)

### 1. Set environment variables

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export TAVILY_API_KEY=tvly-...
```

Optional:
```bash
export DAILY_SPEND_CAP_USD=5.0   # Default $5/day cap on Claude API costs
```

### 2. Start the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload     # Runs on http://localhost:8000
```

Verify: `curl http://localhost:8000/health` should return `{"status":"ok"}`.

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev                       # Runs on http://localhost:5173
```

Open http://localhost:5173 in your browser.

### 4. (Optional) Override the API base URL

If the backend runs on a different host or port, set this before starting the frontend:

```bash
export VITE_API_BASE=http://your-host:8000
```

### 5. (Alternative) Run with Docker

Docker Compose auto-loads `docker-compose.override.yml`, so the bare command is the **dev** stack
(hot reload, source bind-mounted, backend on 8000, Vite on 5173):

```bash
cp .env.example .env          # then fill in the two API keys
docker compose up --build
```

**Production** (nginx on port 80 serving the built SPA and proxying `/api`, backend not exposed)
must skip the override file explicitly:

```bash
docker compose -f docker-compose.yml up --build -d
```

In production, analysis data lives in the named Docker volume `prism-data` (inspect with `docker volume inspect prism-data`; copy out with `docker cp`). In dev it stays in `backend/data/` on the host. Requires Docker Compose v2.24 or newer.

## How It Works

1. **User submits a comparison** — two options and a decision intent.
2. **Tavily web search** runs in parallel for both options, gathering real sources.
3. **Claude analyzes the research** and produces scored criteria with source citations, confidence levels, and an overall winner with reasoning.
4. **Results render in real-time** — the frontend streams progress via SSE while the backend processes.
5. **User refines** — adjust weights, add custom criteria, flag sources, go deeper on a criterion, or view flip analysis to see what would change the winner.

## Architecture

```
Browser (React) ──HTTP──▸ FastAPI backend ──▸ Tavily (web search)
                                           ──▸ Claude (analysis)
                                           ──▸ data/ (JSON files)
```

The frontend is a single-page React app. The backend is a stateless FastAPI service that persists results as JSON files in `data/`. There is no database.

### Data Flow: Single Comparison Request

#### 1. User Submission (Frontend)

The user fills in option A, option B, and intent, then clicks Compare.

```
ComparisonForm.handleSubmit()
  └── useComparison().mutate()          TanStack Query mutation
        └── apiPost('/api/compare', { option_a, option_b, intent })
              └── HTTP POST ──▸ FastAPI backend
```

#### 2. Request Handling (Backend)

The backend validates, deduplicates, and returns immediately.

```
POST /api/compare
  │
  ├── check_spending_cap()              Reject with 429 if daily cap reached
  │
  ├── Dedup check (if not force_refresh)
  │     SHA-256(lower(option_a)|lower(option_b)|lower(intent))[:16]
  │     Scan all data/*.json for matching hash, completed, and < 24h old
  │     If match: stamp tavily_cached_at, return { comparison_id, deduplicated: true }
  │
  ├── Generate UUID comparison_id
  │
  ├── Write initial result to data/{id}.json with status="processing"
  │     (atomic write: tempfile → fsync → os.replace)
  │
  ├── Queue background task: process_comparison()
  │
  └── Return 202 { comparison_id }
```

#### 3. Background Processing (Backend)

The background task runs the full AI pipeline.

```
process_comparison()
  └── generate_comparison()
        │
        ├── Step 1: Web Search (Tavily) ── runs both in parallel via asyncio.gather
        │     search_option(option_a)
        │       query = "{option} hidden costs environmental impact subsidies externalities supply chain"
        │       Check in-memory cache (TTLCache, 200 entries, 24h TTL)
        │       If miss: tavily.search(query, depth="basic", max_results=10)
        │       Cache result with ISO timestamp
        │       Return OptionResearch { results: [{ title, url, content, score }] }
        │     search_option(option_b) ── same flow
        │
        │     Progress messages emitted:
        │       "Searching web for {option_a/b}..."
        │       "Found {n} sources for {option_a/b}"
        │
        │     If both searches fail → write error result, return early
        │
        ├── Step 2: AI Analysis (Claude)
        │     Progress: "Analyzing sources for hidden costs..."
        │
        │     generate_criteria()
        │       Build prompt with research context + source URL allowlist
        │       System prompt: "expert at discovering non-obvious decision criteria..."
        │       User prompt: research for both options, scoring rules, JSON format
        │
        │       claude.messages.create(model="claude-sonnet-4-5-20250929", max_tokens=4096)
        │
        │       record_usage()
        │         Calculate cost from token counts
        │         Persist to data/usage_metrics.json (atomic write)
        │         add_cost() → spending guard daily accumulator
        │
        │       Parse JSON response (strip markdown code blocks if present)
        │       Validate via CriteriaOutput.model_validate()
        │       Returns: { criteria[], winner, reasoning, source_classifications[] }
        │
        │     Progress: "Generated {n} criteria"
        │
        └── Step 3: Package Result
              Progress: "Finalizing comparison..."

              Build source_metadata: { url → SourceMetadata(quality) }
                from Claude's source_classifications

              Build criteria list with confidence levels:
                high:   ≥2 sources AND ≥1 peer-reviewed or government
                medium: ≥1 source AND ≥1 industry or news
                low:    0 sources or only blog/unknown

              Assemble ComparisonResult:
                status="completed", criteria, winner, reasoning,
                research_a/b (cached for Go Deeper), source_metadata

              mark_complete(comparison_id)
              storage.write_result() → data/{id}.json (atomic write)
```

#### 4. Real-Time Progress (Parallel with Step 3)

Two channels keep the frontend updated while the background task runs.

```
SSE Progress Stream:
  useProgress(comparisonId)
    new EventSource('/api/progress/{id}')
      Backend polls progress_store dict every 0.5s
      Yields SSE events as the orchestrator adds messages:
        event: progress  { status: "Searching web for..." }
        event: progress  { status: "Analyzing sources..." }
        event: progress  { status: "Generated 4 criteria" }
        event: complete  { comparison_id }
      Cleans up in-memory store after completion
      Times out after 2 minutes

Result Polling:
  useResults(comparisonId)
    TanStack Query polls GET /api/results/{id} every 1s
    Reads data/{id}.json → ComparisonResult.model_validate()
    While status="processing" → keep polling
    When status="completed" or "error" → stop polling
    Times out after 2 minutes
```

#### 5. Result Display (Frontend)

Once `useResults` returns a completed result, the UI renders.

```
App.tsx renders <ResultsDisplay>
  ├── Winner banner + reasoning
  ├── Criteria cards with scores, weights, confidence badges
  ├── Source links with quality tier indicators
  ├── Weight sliders (recalculate scores client-side, no API call)
  ├── "Go Deeper" → POST /api/comparisons/{id}/go-deeper (adds 2-3 criteria)
  ├── "Regenerate Weights" → POST /api/comparisons/{id}/regenerate-weights
  ├── Flip Analysis → GET /api/comparisons/{id}/flip-analysis
  └── Source flagging → PATCH /api/comparisons/{id}/sources/flag
```

#### Data Written to Disk

```
data/
├── {comparison_id}.json     Written twice: first with status="processing", then "completed"
└── usage_metrics.json       Append-only list of usage records from every Claude API call
```

#### In-Memory State

| Store | Type | Lifecycle |
|-------|------|-----------|
| `progress_store` | `dict[str, list[str]]` | Created per comparison, cleaned up after SSE completes |
| `progress_complete` | `dict[str, bool]` | Same lifecycle as progress_store |
| `_TAVILY_CACHE` | `TTLCache(maxsize=200, ttl=86400)` | 24h TTL, evicts LRU when full |
| `_usage_records` | `list[dict]` | Loaded from disk on startup, appended per API call |
| `_daily_cost_usd` | `float` | Loaded from disk on startup, resets at midnight |

### Backend Structure

```
backend/app/
├── main.py                  FastAPI app, CORS, router registration
├── models.py                All Pydantic models (request/response schemas)
├── storage.py               JSON file persistence with atomic writes
├── routers/
│   ├── comparison.py        Core CRUD + analysis endpoints
│   ├── health.py            Readiness probe
│   ├── monitoring.py        Usage stats and daily spend
│   └── progress.py          SSE progress streaming
└── services/
    ├── config.py             API client singletons (lru_cache)
    ├── tavily_service.py     Web search with in-memory result caching
    ├── claude_service.py     Prompt construction and Claude API calls
    ├── criteria_service.py   Go deeper, regenerate weights
    ├── flip_service.py       Sensitivity analysis and flip suggestions
    ├── orchestrator.py       Coordinates search → analysis → result
    ├── progress_store.py     In-memory SSE event buffer
    ├── spending_guard.py     Daily cost cap enforcement
    └── usage_tracker.py      Token/cost tracking, persisted to disk
```

### Frontend Structure

```
frontend/src/
├── App.tsx                  Root component, routing via React state + URL hash
├── main.tsx                 Entry point, QueryClientProvider
├── lib/
│   ├── api.ts               fetch wrappers (apiGet, apiPost)
│   └── queryClient.ts       TanStack Query configuration
└── features/
    ├── comparison/           Submission form, example prompts, types
    ├── criteria/             Add/edit criteria, go deeper, source links
    ├── flip/                 Flip analysis display
    ├── results/              Result display, polling, scoring explainer
    ├── weights/              Weight sliders, recalculation, regenerate
    ├── progress/             SSE hook and progress display
    └── history/              Sidebar history list
```

## Design Decisions

### No database — JSON file storage

Results are stored as individual JSON files in `data/` (one file per comparison). This keeps the stack simple with zero infrastructure dependencies. Atomic writes (tempfile + fsync + os.replace) prevent corruption on crash. The `data/` directory is gitignored and created at runtime.

### Async processing with polling

`POST /api/compare` returns 202 immediately with a `comparison_id`. The actual work (web search + AI analysis) runs as a FastAPI background task. The frontend polls `GET /api/results/{id}` and displays SSE progress messages in the meantime. This avoids long-lived HTTP connections and keeps the UX responsive.

### Client-side scoring

Weight adjustments recalculate scores entirely in the browser — no API call needed. The backend provides raw scores and weights; the frontend applies the weighted formula. This makes weight sliders feel instant.

### Deduplication

Identical comparisons (same options + intent, case-insensitive) are detected via SHA-256 hash and return the existing result instead of making duplicate API calls. The dedup stamps `tavily_cached_at` so the UI can show when research data is from cache.

### Spending guard

A daily cost cap (default $5, configurable via `DAILY_SPEND_CAP_USD`) prevents runaway API costs. The guard loads accumulated costs from `data/usage_metrics.json` on startup so it survives restarts. Every Claude API call records its token usage and cost, which feeds into both the spending guard and the monitoring endpoint.

### Source confidence scoring

Each criterion gets a confidence level (high/medium/low) based on the number and quality of its sources. Source quality is classified by Claude during analysis (peer-reviewed, government, industry, news, blog). Users can flag individual sources as unreliable, which is persisted with the result.

### URL hash routing

The app uses React state for "routing" with the comparison ID synced to the URL hash (`#comparison-id`). This survives browser refresh without a router library. Important: never use `window.location.reload()` as it breaks React state.

## API Endpoints

### Core
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/compare` | Submit comparison (returns 202 + comparison_id) |
| `GET` | `/api/results/{id}` | Get result (poll until status != "processing") |
| `GET` | `/api/results` | List all comparisons |
| `GET` | `/api/progress/{id}` | SSE progress stream |

### Criteria
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/comparisons/{id}/criteria` | Add custom criterion |
| `PATCH` | `/api/comparisons/{id}/criteria/{cid}` | Edit criterion |
| `DELETE` | `/api/comparisons/{id}/criteria/{cid}` | Delete criterion |

### Analysis
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/comparisons/{id}/go-deeper` | Deep-dive on a criterion |
| `POST` | `/api/comparisons/{id}/regenerate-weights` | AI-regenerate weights |
| `GET` | `/api/comparisons/{id}/flip-analysis` | What would change the winner |
| `PATCH` | `/api/comparisons/{id}/sources/flag` | Flag source as unreliable |

### Ops
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Readiness check |
| `GET` | `/api/monitoring` | Token usage and cost stats |

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend | Python | 3.11+ |
| | FastAPI | 0.128 |
| | Pydantic | 2.12 |
| | Anthropic SDK | 0.75 |
| | Tavily SDK | 0.7 |
| Frontend | React | 19 |
| | Vite | 7 |
| | TypeScript | 5.9 |
| | TanStack Query | 5 |
| | Tailwind CSS | 4 |

## Development

### Type checking

```bash
cd frontend
npx tsc --noEmit
```

### Linting

```bash
cd frontend
npm run lint
```

### Production build

```bash
cd frontend
npm run build        # Output in frontend/dist/
```

### Interactive API docs

With the backend running, visit http://localhost:8000/docs for the auto-generated Swagger UI.
