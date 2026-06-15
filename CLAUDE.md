# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment

**Platform:** Windows — use `;` instead of `&&` when chaining shell commands.

## Project Overview

**Prism** — Unified AI-powered decision analysis tool. Supports N options (2–6+), three depth tiers (Quick/Medium/Deep), and a consumer app UI. Built on FastAPI + React.

## Tech Stack

**Backend:** Python 3.11+, FastAPI, Pydantic v2, `anthropic` SDK, Tavily Search API  
**Frontend:** React 19, Vite 7, TypeScript, TanStack Query v5, Tailwind CSS v4

## Common Commands

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload          # dev server on port 8000
python -c "from app.main import app; print('OK')"  # verify imports
pytest tests/                          # run all tests
pytest tests/test_router.py -k "test_get_analysis_found"  # single test
```

### Frontend
```bash
cd frontend
npm install
npm run dev          # dev server on port 5173
npm run build
npx tsc --noEmit     # type check
```

## Environment Variables

```bash
TAVILY_API_KEY=tvly-...           # https://app.tavily.com/home
ANTHROPIC_API_KEY=sk-ant-...      # https://console.anthropic.com/settings/keys
DAILY_SPEND_CAP_USD=5.0           # optional, default $5/day
```

## API Endpoints

The API uses a **two-level hierarchy**: decisions own analyses.

**Two-step flow to run an analysis:**
1. `POST /api/decisions` → creates the decision, returns `decision_id` + `suggested_tier` + `rationale`
2. `POST /api/decisions/{decision_id}/analyses` → kicks off analysis (202), returns `analysis_id`

**Decisions:**
- `GET /api/decisions` — list all decisions (sorted newest-first)
- `POST /api/decisions` — create decision; auto-suggests tier via claude-haiku

**Analyses:**
- `POST /api/decisions/{decision_id}/analyses` — run analysis for a given tier (202 async)
- `GET /api/decisions/{decision_id}/analyses/{analysis_id}` — poll until `status != "processing"`
- `GET /api/decisions/{decision_id}/analyses` — list analyses for a decision
- `PATCH /api/decisions/{decision_id}/analyses/{analysis_id}/weights` — persist weight overrides
- `POST /api/decisions/{decision_id}/analyses/{analysis_id}/go-deeper` — add more criteria using cached research (Medium/Deep only)
- `POST /api/decisions/{decision_id}/analyses/{analysis_id}/regenerate-weights` — AI re-weights criteria

**Criteria CRUD:**
- `POST /api/decisions/{decision_id}/analyses/{analysis_id}/criteria` — add user criterion
- `PATCH /api/decisions/{decision_id}/analyses/{analysis_id}/criteria/{criterion_id}` — edit
- `DELETE /api/decisions/{decision_id}/analyses/{analysis_id}/criteria/{criterion_id}` — delete

**Progress & Ops:**
- `GET /api/progress/{analysis_id}` — SSE stream of progress messages (event `progress` / `complete` / `error`)
- `GET /health` — readiness check
- `GET /api/monitoring` — token usage and cost stats

## Architecture

### Request flow
```
Frontend                Backend
-------                 -------
POST /api/decisions  →  suggest_tier (haiku) → writes Decision JSON
POST .../analyses    →  FastAPI BackgroundTask
                           orchestrator.run_analysis()
                             quick:  generate_criteria_quick (sonnet)
                             medium: search_all_options (Tavily) → generate_criteria_medium (sonnet)
                             deep:   medium pipeline + discover_hidden_properties (sonnet)
                        → writes AnalysisResult JSON
GET .../analyses/{id} ← poll until status = "completed"
GET /api/progress/{id} ← SSE stream (uses analysis_id as comparison_id parameter)
```

### Storage layout (`backend/data/`)
```
data/
  decisions/
    {decision_uuid}.json          # Decision model
    {decision_uuid}/
      analyses/
        {analysis_uuid}.json      # AnalysisResult model
  usage_metrics.json              # cost tracking (gitignored)
```
Writes are atomic: tempfile + fsync + `os.replace`.

### Tier system
| Tier | Cost | Time | What it does |
|------|------|------|--------------|
| quick | ~$0.002 | ~5s | LLM knowledge only (claude-sonnet), no web search |
| medium | ~$0.04 | ~45s | Tavily web search per option → AI criteria with sources |
| deep | ~$0.18 | ~3min | Medium pipeline + hidden property discovery (systemic second-order effects) |

- Tier is suggested automatically by `suggest_tier.py` (claude-haiku) when the decision is created.
- Hidden properties (Deep only) are best-effort: failure doesn't abort the analysis.
- Dedup: identical options + intent + tier returns a cached `analysis_id` without re-running.

### Key services
- `orchestrator.py` — routes quick/medium/deep pipeline; single entry point `run_analysis()`
- `claude_service.py` — `generate_criteria_quick` / `generate_criteria_medium`; uses prompt caching (`cache_control: ephemeral`) on the system instructions
- `hidden_service.py` — `discover_hidden_properties()`; Deep tier only
- `suggest_tier.py` — auto-tier classification via claude-haiku
- `tavily_service.py` — web search with result caching
- `spending_guard.py` — daily cap; reads `DAILY_SPEND_CAP_USD`, persists across restarts by summing today's records from `usage_metrics.json`
- `storage.py` — `JSONStorage` class; UUID-validated reads/writes; `list_decisions()` / `list_analyses()`

### Frontend structure
- `App.tsx` — single page; hash-based routing (`#decisionId:analysisId`); sidebar history + main content
- `features/comparison/DecisionForm.tsx` — two-API-call form (POST decisions → POST analyses)
- `features/progress/ProgressView.tsx` — SSE consumer; shown while `analysisStarted=true`
- `features/results/ResultsDisplay.tsx` — polls `useResults`; shows `WinnerCard`, `CriteriaSection`, `HiddenPropertiesSection` (Deep only)
- `lib/api.ts` — `apiPost` / `apiGet` helpers; all TypeScript domain types (`AnalysisResult`, `Criterion`, `HiddenProperty`, etc.)

### Scoring
Weights are normalised inside the orchestrator (sum to 1.0) when the analysis is created and stored as `weights_original` and `weights_current`. Client-side recalculation re-applies weights to criteria scores without an API round-trip; `PATCH .../weights` persists user overrides.

## Testing Approach

- Tests live in `backend/tests/`, run from the `backend/` directory with `pytest tests/`
- Mock external APIs (Claude, Tavily) with `monkeypatch` — never hit real APIs in tests
- Tests requiring `ANTHROPIC_API_KEY` are decorated with `@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), ...)`
- Fixtures use `tmp_path` for isolated `JSONStorage` instances; monkeypatch swaps the router's module-level `storage` singleton
