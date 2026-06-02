# Project State: decide/

## Current Status

**Phase 6 of 6 — integration smoke test**  
Last activity: 2026-06-02 — phase-5 committed (Consumer App UI + analyses list endpoint)

**Next action:** Run integration smoke test (see `tasks/PRD.md` Phase 6 checklist)

## Progress

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Scaffold new app from Orchids | ✅ Done |
| 2 | Backend: data model (N options + depth tier) | ✅ Done |
| 3 | Backend: pipeline (Quick + Medium tiers) | ✅ Done |
| 4 | Backend: Deep tier (hidden properties) | ✅ Done |
| 5 | Frontend: Consumer App UI | ✅ Done |
| 6 | Integration + smoke test | ⬜ Next |

## Key Facts

- Endpoint hierarchy: `POST/GET /api/decisions`, `POST/GET /api/decisions/{id}/analyses`, `GET /api/decisions/{id}/analyses/{aid}`
- Three depth tiers: Quick (LLM only ~5s), Medium (Tavily + LLM ~30–60s), Deep (Medium + hidden properties ~2–5min)
- Client-side scoring: weight slider changes recalculate winner without an API call (`lib/scoring.ts`)
- Data lives in `decide/backend/data/` (gitignored)

## Known Limitations

- Prompt caching annotation correct but inactive (system prompt below minimum token threshold)
- AHP pairwise refinement endpoint defined in PRD but not yet implemented
- DELETE criterion has no frontend UI

---
*Tracking doc: `tasks/PRD.md`*  
*Last updated: 2026-06-02*
