---
phase: 06
plan: 01
subsystem: frontend-sse
tags: [sse, eventsource, progress, url-fix, dev-config]

dependency-graph:
  requires:
    - "02-03: SSE progress streaming (FastAPI backend endpoint)"
  provides:
    - "SSE EventSource connecting to absolute backend URL"
  affects: []

tech-stack:
  added: []
  patterns:
    - "Absolute URLs for cross-origin dev server requests (Vite → FastAPI)"

key-files:
  created: []
  modified:
    - frontend/src/features/progress/useProgress.ts

decisions:
  - "Use absolute URL directly in EventSource rather than adding Vite proxy or shared constant — minimal change, matches existing api.ts pattern"

metrics:
  duration: "< 1 minute"
  completed: "2026-02-14"
---

# Phase 6 Plan 01: Fix SSE EventSource URL Summary

**One-liner:** Fixed relative `/api/progress` URL to absolute `http://localhost:8000/api/progress` so SSE connects to FastAPI backend instead of Vite dev server.

## What Was Built

Single-line fix in `useProgress.ts` changing the `EventSource` constructor URL from a relative path (which resolves to the Vite dev server at port 5173) to the absolute backend URL (FastAPI at port 8000).

**Root cause:** Vite's dev server does not proxy `/api/progress/*` to the backend. The relative URL `new EventSource('/api/progress/${id}')` connected to Vite, which has no SSE handler, so the connection silently failed and users saw "Connecting..." indefinitely.

**Fix:** `new EventSource('http://localhost:8000/api/progress/${comparisonId}')` — matches the pattern already used in `api.ts` where all fetch calls use `API_BASE = 'http://localhost:8000'`.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Fix EventSource URL to use absolute backend URL | f90a9af | frontend/src/features/progress/useProgress.ts |

## Verification

- `npx tsc --noEmit` passes — no type errors
- File contains `http://localhost:8000/api/progress`
- No other lines changed (1 insertion, 1 deletion confirmed by git)

## Decisions Made

**Use absolute URL inline** — The plan explicitly ruled out: Vite proxy config, importing `API_BASE`, or creating a shared constants module. The one-line inline change is the minimum viable fix that matches existing patterns in the codebase.

## Deviations from Plan

None — plan executed exactly as written.

## Next Phase Readiness

This is the final planned phase. No blockers. The milestone is now ready for final audit or completion.
