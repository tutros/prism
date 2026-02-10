# Summary: 03-01 Criteria CRUD Backend

## Status: Complete

## What Was Built

Added criteria CRUD backend with origin tracking to distinguish AI-generated from user-created criteria.

### Deliverables

1. **Extended Criterion model** (backend/app/models.py)
   - Added `origin: Literal["ai", "user"] = "ai"` field
   - Created `CriterionCreate` model for POST requests
   - Created `CriterionUpdate` model for PATCH with partial updates

2. **CRUD endpoints** (backend/app/routers/comparison.py)
   - `POST /api/comparisons/{id}/criteria` - Creates user criterion (origin="user")
   - `PATCH /api/comparisons/{id}/criteria/{cid}` - Updates any criterion
   - `DELETE /api/comparisons/{id}/criteria/{cid}` - Removes criterion

3. **Origin tracking in orchestrator** (backend/app/services/orchestrator.py)
   - AI-generated criteria explicitly set `origin="ai"`

4. **Frontend types** (frontend/src/features/comparison/types.ts)
   - Added `origin: 'ai' | 'user'` to Criterion interface

## Commits

| Hash | Description |
|------|-------------|
| b44e4a8 | feat(03-01): extend Criterion model with origin field |
| f3ac31f | feat(03-01): add criteria CRUD endpoints |
| 2c86153 | feat(03-01): set origin=ai on AI-generated criteria |

## Verification

- Backend imports work: `from app.models import Criterion, CriterionCreate, CriterionUpdate`
- TypeScript compiles without errors
- CRUD endpoints respond correctly (POST 201, PATCH 200, DELETE 200)
- Origin field persists in JSON storage

## Key Decisions

- Used Pydantic's `exclude_unset=True` for partial updates via PATCH
- User criteria always get `origin="user"` (enforced server-side)
- UUID used for criterion IDs to avoid collisions
