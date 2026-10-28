# Project State: Prism

## Current Status

**v1.0 MVP shipped 2026-06-15 (untagged; the `v1.0`/`v1.0.1` tags point at the 2026-02 predecessor). No active milestone.**
Last activity: 2026-10-27 — post-v1 hygiene (tests green, stale worktree removed, tier-suggestion parsing fix)

**Next action:** Define milestone v1.1 with the owner. Candidate directions recorded in
`.planning/MILESTONES.md`: database storage, shareable links, user accounts; or a polish
release closing the known limitations below.

## Progress

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Scaffold new app from Orchids | Done |
| 2 | Backend: data model (N options + depth tier) | Done |
| 3 | Backend: pipeline (Quick + Medium tiers) | Done |
| 4 | Backend: Deep tier (hidden properties) | Done |
| 5 | Frontend: Consumer App UI | Done |
| 6 | Bug fixes + 8-file code review (9d394d5) | Done |
| — | Post-v1 hygiene | In review (PR `chore/post-v1-hygiene`) |

## Key Facts

- Endpoint hierarchy: `POST/GET /api/decisions`, `POST/GET /api/decisions/{id}/analyses`, `GET /api/decisions/{id}/analyses/{aid}`
- Three depth tiers: Quick (LLM only ~5s), Medium (Tavily + LLM ~30–60s), Deep (Medium + hidden properties ~2–5min)
- Client-side scoring: weight slider changes recalculate winner without an API call (`lib/scoring.ts`)
- Data lives in `backend/data/` (gitignored)
- Backend tests: `cd backend; venv/Scripts/python -m pytest tests/` (27 tests; 3 are live and skip without `ANTHROPIC_API_KEY`)
- No CI. One vitest file exists (`frontend/src/lib/scoring.test.ts`) but vitest is not installed and there is no `npm test` script, so it never runs

## Known Limitations

- Prompt caching annotation correct but inactive (system prompt below minimum token threshold)
- AHP pairwise refinement endpoint was planned in the original PRD but never implemented
- DELETE criterion route exists in backend but has no frontend UI
- `npm run lint` reports 7 pre-existing errors (React set-state-in-effect, two `any`); tracked as issue #2

---
*Last updated: 2026-10-27*
