import asyncio
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..models import (
    AnalysisResult, Criterion, CriterionCreate, CriterionUpdate,
    Decision, DecisionInput,
)
from ..storage import JSONStorage
from ..services.orchestrator import run_analysis
from ..services.spending_guard import check_spending_cap
from ..services.criteria_service import go_deeper, regenerate_weights
from ..services.suggest_tier import _suggest_tier_async
from ..services.tavily_service import OptionResearch, SearchResult

router = APIRouter(prefix="/api", tags=["decisions"])
storage = JSONStorage()


class _AnalysisInput(BaseModel):
    tier: Literal["quick", "medium", "deep"] = "medium"


def _dedup_key(options: list[str], intent: str, tier: str) -> str:
    joined = "|".join(sorted(o.lower().strip() for o in options))
    raw = f"{joined}|{intent.lower().strip()}|{tier}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


async def _run_analysis_bg(
    analysis_id: str, decision_id: str, options: list[str],
    intent: str, tier: str, option_contexts: dict,
) -> None:
    from ..services.progress_store import mark_complete
    try:
        result = await run_analysis(
            analysis_id=analysis_id,
            decision_id=decision_id,
            options=options,
            intent=intent,
            tier=tier,
            option_contexts=option_contexts,
        )
        storage.write_analysis(result)
    except Exception as e:
        mark_complete(analysis_id)
        storage.write_analysis(AnalysisResult(
            analysis_id=analysis_id,
            decision_id=decision_id,
            tier=tier,
            status="error",
            options=options,
            reasoning=f"Unexpected error: {e}",
            created_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        ))


# ── Decision endpoints ────────────────────────────────────────────────────────

@router.post("/decisions")
async def create_decision(data: DecisionInput):
    """Create a decision and return a tier suggestion."""
    try:
        suggestion = await _suggest_tier_async(
            f"Decision: {data.intent}\nOptions: {', '.join(data.options)}"
        )
        suggested_tier = suggestion["tier"]
        rationale = suggestion["rationale"]
    except Exception:
        suggested_tier = data.tier or "medium"
        rationale = "Unable to auto-suggest tier."

    decision = Decision(
        id=str(uuid.uuid4()),
        title=data.intent[:100],
        options=data.options,
        option_contexts=data.option_contexts,
        intent=data.intent,
        created_at=datetime.now(timezone.utc),
    )
    storage.write_decision(decision)
    return {"decision_id": decision.id, "suggested_tier": suggested_tier, "rationale": rationale}


@router.get("/decisions")
async def list_decisions():
    ids = await asyncio.to_thread(storage.list_decisions)
    decisions = []
    for did in ids:
        d = await asyncio.to_thread(storage.read_decision, did)
        if d:
            decisions.append({
                "decision_id": d.id,
                "title": d.title,
                "options": d.options,
                "intent": d.intent,
                "created_at": d.created_at.isoformat(),
            })
    decisions.sort(key=lambda x: x["created_at"], reverse=True)
    return {"decisions": decisions}


# ── Analysis endpoints ────────────────────────────────────────────────────────

@router.post("/decisions/{decision_id}/analyses", status_code=202)
async def create_analysis(decision_id: str, body: _AnalysisInput, background_tasks: BackgroundTasks):
    decision = storage.read_decision(decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    try:
        check_spending_cap()
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))

    tier = body.tier
    target_key = _dedup_key(decision.options, decision.intent, tier)
    for aid in await asyncio.to_thread(storage.list_analyses, decision_id):
        existing = await asyncio.to_thread(storage.read_analysis, decision_id, aid)
        if existing and existing.status == "completed":
            if _dedup_key(existing.options, decision.intent, existing.tier) == target_key:
                return JSONResponse(status_code=202, content={"analysis_id": aid, "deduplicated": True})

    analysis_id = str(uuid.uuid4())
    storage.write_analysis(AnalysisResult(
        analysis_id=analysis_id,
        decision_id=decision_id,
        tier=tier,
        status="processing",
        options=decision.options,
        created_at=datetime.now(timezone.utc),
    ))

    background_tasks.add_task(
        _run_analysis_bg, analysis_id, decision_id,
        decision.options, decision.intent, tier, decision.option_contexts,
    )
    return JSONResponse(status_code=202, content={"analysis_id": analysis_id})


@router.get("/decisions/{decision_id}/analyses/{analysis_id}")
async def get_analysis(decision_id: str, analysis_id: str):
    result = storage.read_analysis(decision_id, analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.patch("/decisions/{decision_id}/analyses/{analysis_id}/weights")
async def update_weights(decision_id: str, analysis_id: str, body: dict):
    result = storage.read_analysis(decision_id, analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    result.weights_current = body.get("weights_current", result.weights_current)
    storage.write_analysis(result)
    return result


@router.post("/decisions/{decision_id}/analyses/{analysis_id}/go-deeper")
async def go_deeper_endpoint(decision_id: str, analysis_id: str):
    result = storage.read_analysis(decision_id, analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if result.status != "completed":
        raise HTTPException(status_code=409, detail="Analysis still processing")
    if not result.research:
        raise HTTPException(status_code=400, detail="No cached research (Quick tier cannot go deeper)")

    decision = storage.read_decision(decision_id)
    intent = decision.intent if decision else ""

    research_by_option = {
        opt: OptionResearch(
            option=opt,
            results=[SearchResult(**r) for r in data.get("results", [])],
            error=data.get("error"),
        )
        for opt, data in result.research.items()
    }

    try:
        new_criteria = await go_deeper(
            options=result.options,
            intent=intent,
            research_by_option=research_by_option,
            existing_criteria=result.criteria,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI analysis failed: {e}")

    result.criteria.extend(new_criteria)
    storage.write_analysis(result)
    return result


@router.post("/decisions/{decision_id}/analyses/{analysis_id}/regenerate-weights")
async def regenerate_weights_endpoint(decision_id: str, analysis_id: str):
    result = storage.read_analysis(decision_id, analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if result.status != "completed":
        raise HTTPException(status_code=409, detail="Analysis still processing")
    if not result.criteria:
        raise HTTPException(status_code=400, detail="No criteria to weight")

    decision = storage.read_decision(decision_id)
    intent = decision.intent if decision else ""

    try:
        new_weights = await regenerate_weights(criteria=result.criteria, intent=intent)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI analysis failed: {e}")

    result.weights_current = new_weights
    for c in result.criteria:
        if c.id in new_weights:
            c.weight = new_weights[c.id]
    storage.write_analysis(result)
    return result


# ── Criteria CRUD ─────────────────────────────────────────────────────────────

@router.post("/decisions/{decision_id}/analyses/{analysis_id}/criteria", status_code=201)
async def add_criterion(decision_id: str, analysis_id: str, data: CriterionCreate):
    result = storage.read_analysis(decision_id, analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    criterion = Criterion(
        id=str(uuid.uuid4()), name=data.name, description=data.description,
        scores=data.scores, weight=data.weight, sources=[], origin="user",
    )
    result.criteria.append(criterion)
    storage.write_analysis(result)
    return criterion


@router.patch("/decisions/{decision_id}/analyses/{analysis_id}/criteria/{criterion_id}")
async def update_criterion(decision_id: str, analysis_id: str, criterion_id: str, data: CriterionUpdate):
    result = storage.read_analysis(decision_id, analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    criterion = next((c for c in result.criteria if c.id == criterion_id), None)
    if not criterion:
        raise HTTPException(status_code=404, detail="Criterion not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(criterion, field, value)
    storage.write_analysis(result)
    return criterion


@router.delete("/decisions/{decision_id}/analyses/{analysis_id}/criteria/{criterion_id}")
async def delete_criterion(decision_id: str, analysis_id: str, criterion_id: str):
    result = storage.read_analysis(decision_id, analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    original = len(result.criteria)
    result.criteria = [c for c in result.criteria if c.id != criterion_id]
    if len(result.criteria) == original:
        raise HTTPException(status_code=404, detail="Criterion not found")
    storage.write_analysis(result)
    return {"deleted": criterion_id}
