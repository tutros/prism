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
- Data lives in `backend/data/` (gitignored); production Docker uses the named volume `prism-data` at `/app/data`
- Backend tests: `cd backend; venv/Scripts/python -m pytest tests/` (32 tests; 3 are live and skip without `ANTHROPIC_API_KEY`, 1 needs Docker and skips without it)
- No CI. One vitest file exists (`frontend/src/lib/scoring.test.ts`) but vitest is not installed and there is no `npm test` script, so it never runs

## Known Limitations

- Prompt caching annotation correct but inactive (system prompt below minimum token threshold)
- AHP pairwise refinement endpoint was planned in the original PRD but never implemented
- Criteria CRUD (incl. DELETE), go-deeper, regenerate-weights and PATCH weights routes exist with no frontend UI; see PROJECT.md "Not shipped in v1.0"
- `npm run lint` is clean (issue #2, PR #7). Type check is `npx tsc -b`; `tsc --noEmit` checks nothing (references-only root tsconfig)
- `frontend/src/lib/scoring.test.ts` cannot run: vitest is not installed, there is no `test` script, and `tsconfig.app.json` excludes it. Wire it up with CI (trigger in closed issue #2)

---
*Last updated: 2026-10-29*
