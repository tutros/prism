# Prism

An AI-powered decision comparison tool that surfaces hidden costs and systemic impacts invisible in traditional comparisons.

Enter two to six options (the API accepts up to ten) and your intent (e.g. "buying a house vs. renting, optimizing for 10-year financial outcome"). Prism suggests a depth tier, researches the options via web search (Medium and Deep tiers), then uses Claude to generate scored criteria covering financial, environmental, social, and long-term factors you might not have considered. The Deep tier also surfaces hidden systemic properties: second-order effects of each option.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20.19+ or 22.12+ (required by Vite 7)
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
must skip the override file explicitly. UI and API are served from one origin; the CSP and
backend CORS settings assume this, so a split frontend/backend deployment is not supported:

```bash
docker compose -f docker-compose.yml up --build -d
```

In production, analysis data lives in the named Docker volume `prism-data` (Compose prefixes it with the project name; find it with `docker volume ls --filter name=prism-data`, copy out with `docker cp`). In dev it stays in `backend/data/` on the host. Requires Docker Compose v2.24.4 or newer (for the `!override` tag).

## Security: local use only

Prism has **no authentication**. Every endpoint, including `/api/monitoring` (usage and cost stats), is open to anyone who can reach the server, and every analysis spends your Anthropic and Tavily credit. Run it on `localhost` or a private network only. `DAILY_SPEND_CAP_USD` is not access control and only partly limits spending (see Spending guard below). If you expose it beyond that, put it behind an authenticating reverse proxy first.

To report a security problem, please open a [private security advisory](https://github.com/tutros/prism/security/advisories/new) rather than a public issue.

## How It Works

1. **Create a decision**: options plus intent. Claude Haiku suggests a tier (Quick, Medium or Deep) with a rationale.
2. **Run an analysis** at the chosen tier. The backend returns `202` with an `analysis_id` and works in a background task.
3. **Watch progress** over Server-Sent Events while the frontend polls for the result.
4. **Read the result**: a winner with reasoning, scored criteria with sources, and (Deep only) hidden properties.

### Tiers

| Tier | Approx. cost | Approx. time | What it does |
|------|--------------|--------------|--------------|
| Quick | ~$0.002 | ~5s | Claude's own knowledge, no web search |
| Medium | ~$0.04 | ~45s | Tavily web search per option, then criteria with cited sources |
| Deep | ~$0.18 | ~3min | Medium, plus discovery of hidden systemic properties (best-effort: a failure here doesn't fail the analysis) |

Costs and times are rough guides, not measurements.

## Architecture

```
Browser (React) --HTTP/SSE--> FastAPI backend --> Tavily (web search)
                                              --> Claude (analysis)
                                              --> data/ (JSON files)
```

The backend persists everything as JSON files; there is no database. Decisions own analyses:

```
data/
  decisions/
    {decision_id}.json            Decision (options, intent, suggested tier)
    {decision_id}/analyses/
      {analysis_id}.json          AnalysisResult (written as "processing", then "completed" or "error")
  usage_metrics.json              Token usage and cost per Claude call
```

Writes are atomic (tempfile, fsync, `os.replace`), and IDs are validated as UUIDs before any file access.

### Backend

```
backend/app/
  main.py                  FastAPI app, CORS, router registration
  models.py                Pydantic v2 models
  storage.py               JSONStorage: atomic, UUID-validated reads and writes
  routers/
    comparison.py          Decisions, analyses, criteria, weights
    progress.py            SSE progress stream
    monitoring.py          Usage and daily spend
    health.py              Readiness probe
  services/
    orchestrator.py        run_analysis(): routes the quick / medium / deep pipeline
    suggest_tier.py        Tier suggestion (Claude Haiku)
    claude_service.py      Criteria generation (Claude Sonnet, prompt caching)
    hidden_service.py      Hidden property discovery (Deep only)
    criteria_service.py    Go deeper, regenerate weights
    tavily_service.py      Web search with a 24h in-memory cache
    spending_guard.py      Daily cost cap
    usage_tracker.py       Token and cost tracking, persisted to disk
    progress_store.py      In-memory SSE message buffer
    config.py              API client singletons
```

### Frontend

```
frontend/src/
  App.tsx                  Single page; hash routing (#decisionId:analysisId); history sidebar
  lib/api.ts               apiGet / apiPost helpers and all domain types
  lib/scoring.ts           Client-side weighted scoring
  features/
    comparison/            DecisionForm: create decision, then start analysis
    progress/              SSE consumer and progress view
    results/               Winner card, criteria, hidden properties; polling hook
    history/               Past decisions in the sidebar
```

## Design Decisions

- **No database.** JSON files keep the stack free of infrastructure; atomic writes prevent corruption on crash.
- **Async with polling.** Analyses take seconds to minutes, so the API answers `202` at once and the client polls (with SSE for progress messages).
- **Deduplication.** Starting an analysis at a tier that already has a completed analysis for the same decision returns the existing `analysis_id` instead of spending again.
- **Spending guard.** A daily cap (default $5, `DAILY_SPEND_CAP_USD`) rejects new analyses with `429` once reached; requests that match a completed analysis still get it back, since they cost nothing. It rebuilds today's total from `usage_metrics.json` on startup, so it survives restarts. Limits: only starting an analysis checks the cap, so go-deeper and regenerate-weights (counted) and the tier-suggestion call on every new decision (not counted) still run past it; Tavily usage is not counted; analyses already running can overshoot it.
- **Confidence.** Criteria carry a `confidence` field, but confidence scoring is not implemented yet: AI-generated criteria are all marked `low`. Deep-tier hidden properties get their confidence from Claude.

## API Endpoints

The web UI uses the decision, analysis and progress endpoints. The weights, criteria, go-deeper and regenerate-weights endpoints are API-only for now. Full schemas are at http://localhost:8000/docs while the backend runs.

### Decisions and analyses
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/decisions` | Create a decision; returns `decision_id`, `suggested_tier`, `rationale` |
| `GET` | `/api/decisions` | List decisions, newest first |
| `POST` | `/api/decisions/{decision_id}/analyses` | Start an analysis at a tier (`202` + `analysis_id`) |
| `GET` | `/api/decisions/{decision_id}/analyses` | List a decision's analyses |
| `GET` | `/api/decisions/{decision_id}/analyses/{analysis_id}` | Get a result; poll until `status != "processing"` |
| `GET` | `/api/progress/{analysis_id}` | SSE stream (`progress` / `complete` / `error` events) |

### Refining a result (API-only)
| Method | Path | Description |
|--------|------|-------------|
| `PATCH` | `.../analyses/{analysis_id}/weights` | Persist weight overrides |
| `POST` | `.../analyses/{analysis_id}/go-deeper` | Add criteria from cached research (Medium/Deep) |
| `POST` | `.../analyses/{analysis_id}/regenerate-weights` | Let Claude re-weight the criteria |
| `POST` | `.../analyses/{analysis_id}/criteria` | Add a criterion |
| `PATCH` | `.../analyses/{analysis_id}/criteria/{criterion_id}` | Edit a criterion |
| `DELETE` | `.../analyses/{analysis_id}/criteria/{criterion_id}` | Delete a criterion |

`...` is `/api/decisions/{decision_id}`.

### Ops
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Readiness check |
| `GET` | `/api/monitoring` | Token usage and cost stats (unauthenticated; see Security) |

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

```bash
# Backend tests. Most mock Claude and Tavily; a few live tests also call the real
# Anthropic API when ANTHROPIC_API_KEY is set, so unset it to stay offline.
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/

# Frontend
cd frontend
npx tsc -b         # type check (tsconfig.json is references-only; plain `tsc --noEmit` checks nothing)
npm run lint
npm run build      # output in frontend/dist/
```

## License

[MIT](LICENSE)
