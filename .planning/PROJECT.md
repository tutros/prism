# Hidden Cost Comparator

## What This Is

A web app that helps users compare two options by surfacing hidden costs and non-obvious systemic impacts. Uses AI (Claude) to research options via web search (Tavily), generate 3-5 non-obvious criteria with source citations, and present interactive results with adjustable weights, flip detection, and source quality signals. Users can go deeper for more criteria, edit criteria inline, and see what realistic actions would reverse the winner.

## Core Value

Surface the invisible threads that connect everyday choices to systemic impacts — the things people don't think about when making decisions.

## Requirements

### Validated

- User can enter two options to compare — v1.0
- User can describe their intent/priorities — v1.0
- AI researches both options using web search with sources — v1.0
- AI generates 3-5 non-obvious criteria relevant to the options — v1.0
- Criteria focus on hidden costs (embedded energy, subsidies, externalities) — v1.0
- AI weights criteria based on user intent — v1.0
- User can adjust weights via sliders — v1.0
- Weights auto-recalculate winner when adjusted — v1.0
- User can regenerate weights (re-prompts AI with intent) — v1.0
- System shows winning option with reasoning — v1.0
- System shows what would flip the outcome for losing option — v1.0
- Flip suggestions are realistic and actionable — v1.0
- All information includes sources — v1.0
- Sources display quality indicators (6 tiers) — v1.0
- User can "go deeper" to get more criteria — v1.0
- User can add/edit custom criteria alongside AI-generated — v1.0
- Results saved to file for later recall — v1.0
- Loading states and streaming progress during AI processing — v1.0
- Mobile responsive design — v1.0
- Example prompts to help users get started — v1.0
- Token usage tracking and daily spending cap — v1.0
- Tavily result caching with cache age indicator — v1.0
- Monitoring dashboard for cost visibility — v1.0
- User can flag unreliable sources — v1.0

### Active

(None yet — define with next milestone)

### Out of Scope

- Database storage — POC uses file-based persistence
- User accounts / authentication — anyone can use
- Shareable links — future enhancement after database
- More than 2 options — keep it simple for now
- Mobile app — web-first
- Real-time price tracking — maintenance burden, out of core value
- Collaborative editing — scope creep

## Context

**Shipped v1.0** with ~3,640 LOC (1,860 Python + 1,780 TypeScript) across 60 files.

**Tech stack:** React 19 + Vite 7 + Tailwind v4 + TanStack Query v5 (frontend), Python 3.11+ + FastAPI 0.128+ (backend), Claude API + Tavily Search API.

**Architecture:** POST returns 202 + comparison_id, frontend polls for results. SSE for real-time progress. Client-side scoring for instant weight recalculation. Atomic JSON writes for crash safety. File-based persistence (data/ directory, gitignored).

**Known limitations:**
- Prompt caching annotation correct but inactive (system prompt below minimum token threshold)
- DELETE criteria route exists in backend but no frontend UI (not required)

## Constraints

- **Tech Stack:** React + Vite + Tailwind (frontend), Python + FastAPI (backend)
- **AI Provider:** Claude API for reasoning and synthesis
- **Search Provider:** Tavily API for sourced web search
- **POC Persistence:** File-based (JSON files) — no database yet
- **Scope:** 3-5 criteria initially, "go deeper" for more

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| React + Vite over Next.js | Simpler setup for POC, separate frontend/backend | Good |
| Python + FastAPI for backend | Great for AI integration, async-native | Good |
| Claude + Tavily for AI + search | Claude for reasoning, Tavily for sourced research | Good |
| File-based persistence for POC | Avoid database complexity, migrate later | Good (sufficient for POC) |
| 3-5 criteria default | Exhaustive analysis overwhelming, option to go deeper | Good |
| Sliders + auto-recalc for weights | Immediate feedback, intuitive UX | Good |
| 202 Accepted + polling pattern | Async processing for slow AI calls | Good |
| Atomic writes (tempfile + fsync + replace) | Crash-safe file persistence | Good |
| Client-side scoring service | Instant weight recalculation without API calls | Good |
| SSE for progress streaming | Real-time feedback during AI processing | Good (after URL fix) |
| Tailwind v4 with @tailwindcss/vite | Modern CSS, no PostCSS config needed | Good |
| 6-tier source quality classification | AI classifies during generation, not domain heuristics | Good |
| TTLCache for Tavily results | 24h cache avoids duplicate web searches | Good |
| Daily spending cap with 429 response | Prevents runaway API costs | Good |

---
*Last updated: 2026-02-14 after v1.0 milestone*
