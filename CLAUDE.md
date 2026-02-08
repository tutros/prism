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

Hidden Cost Comparator - An AI-powered decision comparison tool that surfaces hidden costs and systemic impacts invisible in traditional comparisons.

**Core value:** Surface the invisible threads that connect everyday choices to systemic impacts.

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
orchids-option-analysis-ui/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry
│   │   ├── models.py            # Pydantic models
│   │   ├── storage.py           # JSON file storage
│   │   ├── routers/
│   │   │   ├── comparison.py    # /api/compare, /api/results
│   │   │   └── progress.py      # /api/progress/{id} (SSE)
│   │   └── services/
│   │       ├── config.py        # API client singletons
│   │       ├── tavily_service.py    # Web search
│   │       ├── claude_service.py    # Criteria generation
│   │       ├── orchestrator.py      # Search + AI pipeline
│   │       └── progress_store.py    # SSE progress tracking
│   ├── data/                    # JSON result storage (gitignored)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── features/
│   │   │   ├── comparison/      # Form, types
│   │   │   ├── results/         # Display, polling
│   │   │   ├── weights/         # Sliders, recalculation
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

- `POST /api/compare` - Submit comparison (returns 202 + comparison_id)
- `GET /api/results/{id}` - Get comparison result (poll until status != processing)
- `GET /api/results` - List all comparisons
- `GET /api/progress/{id}` - SSE stream for real-time progress

## Key Patterns

- **Async processing:** POST returns 202, frontend polls for results
- **SSE progress:** Real-time status updates during AI processing
- **Client-side scoring:** Weight changes recalculate instantly without API calls
- **Atomic JSON storage:** Tempfile + fsync + os.replace for crash safety
- **API client singletons:** lru_cache for efficient reuse
