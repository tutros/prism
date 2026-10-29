# Prism

## What This Is

A web app that helps users compare N options (2–6+) by surfacing hidden costs and non-obvious systemic impacts. Uses AI (Claude) to research options via web search (Tavily), generate non-obvious criteria with source citations, and present interactive results with adjustable weights, flip detection, and source quality signals. Three depth tiers let users trade speed for depth. Users can go deeper for more criteria, edit criteria inline, and see what realistic actions would reverse the winner.

## Core Value

Surface the invisible threads that connect everyday choices to systemic impacts — the things people don't think about when making decisions.

## Requirements

### Validated

- User can compare N options (2–6+) — v1.0
- User can describe their intent/priorities — v1.0
- System auto-suggests the appropriate depth tier — v1.0
- Three depth tiers: Quick (LLM-only), Medium (web search), Deep (hidden properties) — v1.0
- AI researches all options using web search with sources (Medium/Deep) — v1.0
- AI generates non-obvious criteria relevant to the options — v1.0
- Criteria focus on hidden costs (embedded energy, subsidies, externalities) — v1.0
- Deep tier discovers hidden systemic second-order impacts — v1.0
- AI weights criteria based on user intent — v1.0
- User can adjust weights via sliders — v1.0
- Weights auto-recalculate winner when adjusted — v1.0
- System shows winning option with reasoning — v1.0
- All information includes sources — v1.0
- Results saved to file for later recall — v1.0
- Multiple analyses per decision (re-run at different tiers) — v1.0
- Loading states and streaming progress during AI processing — v1.0
- Mobile responsive design — v1.0
- Token usage tracking and daily spending cap — v1.0
- Tavily result caching with cache age indicator — v1.0
- Monitoring dashboard for cost visibility — v1.0

### Not shipped in v1.0 (candidates for v1.1)

Listed as validated until 2026-10-29, but the UI for each was the predecessor's two-option
interface, unmounted since the N-option rebuild and deleted in issue #4. Backend status per item:

- User can regenerate weights (re-prompts AI with intent) — route exists
- User can "go deeper" to get more criteria — route exists
- User can add/edit custom criteria alongside AI-generated — routes exist
- Weight changes persist (`PATCH .../weights`) — route exists; sliders are client-only today
- Example prompts to help users get started — frontend only
- System shows what would flip the outcome for losing option, with realistic suggestions — no backend
- User can flag unreliable sources — no backend
- Sources display quality indicators (6 tiers) — no backend (analysis sources are plain URLs)

### Active

(None yet — define with next milestone)

### Out of Scope

- Database storage — POC uses file-based persistence
- User accounts / authentication — anyone can use
- Shareable links — future enhancement after database
- Mobile app — web-first
- Real-time price tracking — maintenance burden, out of core value
- Collaborative editing — scope creep

## Context

**Shipped v1.0** built on FastAPI + React 19.

**Tech stack:** React 19 + Vite 7 + Tailwind v4 + TanStack Query v5 (frontend), Python 3.11+ + FastAPI (backend), Claude API + Tavily Search API.

**Architecture:** Two-level hierarchy — decisions own analyses. POST `/api/decisions` creates the decision and suggests a tier. POST `/api/decisions/{id}/analyses` kicks off the async analysis (202). Frontend polls until status != "processing"; SSE stream provides real-time progress. Client-side scoring for instant weight recalculation. Atomic JSON writes for crash safety. File-based persistence (`data/` directory, gitignored).

**Known limitations:**
- Prompt caching annotation correct but inactive (system prompt below minimum token threshold)
- DELETE criteria route exists in backend but no frontend UI (not required)

## Constraints

- **Tech Stack:** React + Vite + Tailwind (frontend), Python + FastAPI (backend)
- **AI Provider:** Claude API for reasoning and synthesis
- **Search Provider:** Tavily API for sourced web search
- **POC Persistence:** File-based (JSON files) — no database yet
- **Scope:** Configurable criteria count, "go deeper" for more

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| React + Vite over Next.js | Simpler setup for POC, separate frontend/backend | Good |
| Python + FastAPI for backend | Great for AI integration, async-native | Good |
| Claude + Tavily for AI + search | Claude for reasoning, Tavily for sourced research | Good |
| File-based persistence for POC | Avoid database complexity, migrate later | Good (sufficient for POC) |
| Three depth tiers (Quick/Medium/Deep) | Users choose speed vs depth; haiku suggests tier automatically | Good |
| Decisions → Analyses hierarchy | Enables re-running at different tiers, dedup, history | Good |
| Sliders + auto-recalc for weights | Immediate feedback, intuitive UX | Good |
| 202 Accepted + polling pattern | Async processing for slow AI calls | Good |
| Atomic writes (tempfile + fsync + replace) | Crash-safe file persistence | Good |
| Client-side scoring service | Instant weight recalculation without API calls | Good |
| SSE for progress streaming | Real-time feedback during AI processing | Good |
| Tailwind v4 with @tailwindcss/vite | Modern CSS, no PostCSS config needed | Good |
| 6-tier source quality classification | AI classifies during generation, not domain heuristics | Good |
| TTLCache for Tavily results | 24h cache avoids duplicate web searches | Good |
| Daily spending cap with 429 response | Prevents runaway API costs | Good |
| N-option support (2–6+) | Broadens use cases beyond binary comparisons | Good |

---
*Last updated: 2026-06-15 to reflect current Prism architecture (N options, 3 tiers, decisions→analyses API)*
