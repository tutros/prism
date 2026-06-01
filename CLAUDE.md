# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Development Environment

**Platform:** Windows

When running multiple shell commands on one line, use `;` instead of `&&`:
```bash
# Correct (Windows compatible)
cd backend; uvicorn app.main:app --reload

# Wrong (fails on Windows in some contexts)
cd backend && uvicorn app.main:app --reload
```

## Project Overview

**decide/** — Unified AI-powered decision analysis tool. Supports N options (2–5+), three depth tiers (Quick/Medium/Deep), Consumer App UI, and plugs in AHP weight refinement + hidden property discovery.

Built by extending Orchids (`orchids-option-analysis-ui`). See `../tasks/PRD.md` for full requirements and `../tasks/todo.md` for build plan.

## Tech Stack

**Backend:**
- Python 3.11+
- FastAPI 0.128+
- Pydantic v2
- Claude API (anthropic)
- Tavily Search API

**Frontend:**
- React 19
- Vite 7
- TypeScript
- TanStack Query v5
- Tailwind CSS v4

## Common Commands

### Backend
```bash
cd backend
pip install -r requirements.txt    # Install dependencies
uvicorn app.main:app --reload      # Start dev server (port 8000)
python -c "from app.main import app; print('OK')"  # Verify imports
```

### Frontend
```bash
cd frontend
npm install          # Install dependencies
npm run dev          # Start dev server (port 5173)
npm run build        # Production build
npx tsc --noEmit     # Type check
```

## Project Structure

```
decide/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry
│   │   ├── models.py            # Pydantic models
│   │   ├── storage.py           # JSON file storage
│   │   ├── routers/
│   │   │   ├── comparison.py    # /api/compare, /api/results, criteria, sources, flip
│   │   │   ├── health.py        # /health readiness check
│   │   │   ├── monitoring.py    # /api/monitoring usage & cost stats
│   │   │   └── progress.py      # /api/progress/{id} (SSE)
│   │   └── services/
│   │       ├── config.py            # API client singletons
│   │       ├── tavily_service.py    # Web search + result caching
│   │       ├── claude_service.py    # AI criteria generation
│   │       ├── criteria_service.py  # Criteria add/edit/delete logic
│   │       ├── flip_service.py      # Flip analysis (what changes the winner)
│   │       ├── orchestrator.py      # Search + AI pipeline
│   │       ├── progress_store.py    # SSE progress tracking
│   │       ├── spending_guard.py    # Daily API cost budget guard
│   │       └── usage_tracker.py     # Token usage & cost metrics
│   ├── data/                    # JSON result storage (gitignored)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── features/
│   │   │   ├── comparison/      # Form, types, example prompts
│   │   │   ├── criteria/        # Add/edit criteria, go deeper, source links
│   │   │   ├── flip/            # Flip analysis display
│   │   │   ├── results/         # Display, polling, scoring explainer
│   │   │   ├── weights/         # Sliders, recalculation, regenerate
│   │   │   ├── progress/        # SSE hook, display
│   │   │   └── history/         # Sidebar, recall
│   │   └── lib/
│   │       ├── api.ts           # API helpers
│   │       └── queryClient.ts   # TanStack Query
│   └── package.json
└── .planning/                   # GSD planning docs
```

## Environment Variables

Required for AI features:
```bash
TAVILY_API_KEY=tvly-...      # https://app.tavily.com/home
ANTHROPIC_API_KEY=sk-ant-... # https://console.anthropic.com/settings/keys
```

## API Endpoints

**Core:**
- `POST /api/compare` - Submit comparison (returns 202 + comparison_id)
- `GET /api/results/{id}` - Get comparison result (poll until status != processing)
- `GET /api/results` - List all comparisons
- `GET /api/progress/{id}` - SSE stream for real-time progress

**Criteria:**
- `POST /api/comparisons/{id}/criteria` - Add custom criterion
- `PATCH /api/comparisons/{id}/criteria/{criterion_id}` - Edit criterion
- `DELETE /api/comparisons/{id}/criteria/{criterion_id}` - Delete criterion (no frontend UI yet)

**Analysis:**
- `POST /api/comparisons/{id}/go-deeper` - Deep-dive analysis on a criterion
- `POST /api/comparisons/{id}/regenerate-weights` - AI-regenerate weights
- `GET /api/comparisons/{id}/flip-analysis` - What would change the winner
- `PATCH /api/comparisons/{id}/sources/flag` - Flag a source as unreliable

**Ops:**
- `GET /health` - Readiness check
- `GET /api/monitoring` - Token usage and cost stats

## Key Patterns

- **Async processing:** POST returns 202, frontend polls for results
- **SSE progress:** Real-time status updates during AI processing
- **Client-side scoring:** Weight changes recalculate instantly without API calls
- **Atomic JSON storage:** Tempfile + fsync + os.replace for crash safety
- **API client singletons:** lru_cache for efficient reuse
- **Spending guard:** Daily budget cap on API costs, loaded from disk on restart
- **Dedup:** Identical comparisons return cached results (stamps tavily_cached_at explicitly)
