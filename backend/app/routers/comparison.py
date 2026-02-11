from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uuid
from datetime import datetime

from ..models import (
    ComparisonInput, ComparisonResult, Criterion, CriterionCreate, CriterionUpdate,
    FlipAnalysisResponse, ActionableSuggestionModel, SourceMetadata
)
from ..storage import JSONStorage
from ..services.orchestrator import generate_comparison
from ..services.criteria_service import go_deeper, regenerate_weights
from ..services.tavily_service import OptionResearch, SearchResult
from ..services.flip_service import (
    calculate_sensitivity, calculate_flip_analysis, generate_actionable_suggestions
)


class SourceFlagRequest(BaseModel):
    """Request body for flagging a source URL."""
    url: str
    flagged: bool

router = APIRouter(prefix="/api", tags=["comparison"])
storage = JSONStorage()


async def process_comparison(comparison_id: str, data: ComparisonInput) -> None:
    """Process comparison using AI orchestrator."""
    result = await generate_comparison(
        comparison_id=comparison_id,
        option_a=data.option_a,
        option_b=data.option_b,
        intent=data.intent,
    )
    storage.write_result(comparison_id, result)


@router.post("/compare")
async def submit_comparison(
    data: ComparisonInput,
    background_tasks: BackgroundTasks,
):
    comparison_id = str(uuid.uuid4())

    # Write initial "processing" status immediately
    initial = ComparisonResult(
        comparison_id=comparison_id,
        status="processing",
        option_a_name=data.option_a,
        option_b_name=data.option_b,
        intent=data.intent,
        criteria=[],
        winner=None,
        reasoning="",
        created_at=datetime.now(),
        completed_at=None,
    )
    storage.write_result(comparison_id, initial)

    # Queue AI processing in background
    background_tasks.add_task(process_comparison, comparison_id, data)

    return JSONResponse(
        status_code=202,
        content={"comparison_id": comparison_id},
    )


@router.get("/results/{comparison_id}")
async def get_results(comparison_id: str):
    result = storage.read_result(comparison_id)
    if not result:
        raise HTTPException(status_code=404, detail="Comparison not found")
    return result


@router.get("/results")
async def list_results():
    """List all saved comparisons with metadata."""
    comparison_ids = storage.list_results()
    results = []
    for cid in comparison_ids:
        result = storage.read_result(cid)
        if result:
            results.append({
                "comparison_id": result.comparison_id,
                "option_a_name": result.option_a_name,
                "option_b_name": result.option_b_name,
                "status": result.status,
                "created_at": result.created_at.isoformat() if result.created_at else None,
            })
    # Sort by created_at descending (most recent first)
    results.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return {"comparisons": results}


@router.post("/comparisons/{comparison_id}/criteria", status_code=201)
async def add_criterion(comparison_id: str, data: CriterionCreate):
    """Add a new user-created criterion to a comparison."""
    result = storage.read_result(comparison_id)
    if not result:
        raise HTTPException(status_code=404, detail="Comparison not found")

    # Create new criterion with generated ID and origin="user"
    new_criterion = Criterion(
        id=str(uuid.uuid4()),
        name=data.name,
        description=data.description,
        score_a=data.score_a,
        score_b=data.score_b,
        weight=data.weight,
        sources=[],
        origin="user",
    )

    result.criteria.append(new_criterion)
    storage.write_result(comparison_id, result)
    return new_criterion


@router.patch("/comparisons/{comparison_id}/criteria/{criterion_id}")
async def update_criterion(
    comparison_id: str, criterion_id: str, data: CriterionUpdate
):
    """Update an existing criterion (partial update)."""
    result = storage.read_result(comparison_id)
    if not result:
        raise HTTPException(status_code=404, detail="Comparison not found")

    # Find the criterion
    criterion = next((c for c in result.criteria if c.id == criterion_id), None)
    if not criterion:
        raise HTTPException(status_code=404, detail="Criterion not found")

    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(criterion, field, value)

    storage.write_result(comparison_id, result)
    return criterion


@router.delete("/comparisons/{comparison_id}/criteria/{criterion_id}")
async def delete_criterion(comparison_id: str, criterion_id: str):
    """Delete a criterion from a comparison."""
    result = storage.read_result(comparison_id)
    if not result:
        raise HTTPException(status_code=404, detail="Comparison not found")

    # Find and remove the criterion
    original_count = len(result.criteria)
    result.criteria = [c for c in result.criteria if c.id != criterion_id]

    if len(result.criteria) == original_count:
        raise HTTPException(status_code=404, detail="Criterion not found")

    storage.write_result(comparison_id, result)
    return {"deleted": criterion_id}


@router.patch("/comparisons/{comparison_id}/sources/flag")
async def flag_source(comparison_id: str, data: SourceFlagRequest):
    """Toggle the flagged state of a source URL in a comparison."""
    result = storage.read_result(comparison_id)
    if not result:
        raise HTTPException(status_code=404, detail="Comparison not found")

    # Set or update metadata for this URL
    if data.url in result.source_metadata:
        result.source_metadata[data.url].flagged = data.flagged
    else:
        result.source_metadata[data.url] = SourceMetadata(flagged=data.flagged)

    storage.write_result(comparison_id, result)
    return {"url": data.url, "flagged": data.flagged}


def _dict_to_option_research(data: dict) -> OptionResearch:
    """Convert cached research dict back to OptionResearch."""
    return OptionResearch(
        option=data.get("option", ""),
        results=[
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                content=r.get("content", ""),
                score=r.get("score", 0.0),
            )
            for r in data.get("results", [])
        ],
        error=data.get("error"),
    )


@router.post("/comparisons/{comparison_id}/go-deeper")
async def go_deeper_endpoint(comparison_id: str):
    """Generate 2-3 additional criteria using cached research."""
    result = storage.read_result(comparison_id)
    if not result:
        raise HTTPException(status_code=404, detail="Comparison not found")

    # Check for cached research
    if not result.research_a or not result.research_b:
        raise HTTPException(
            status_code=400,
            detail="Re-run comparison to use Go Deeper (no cached research)"
        )

    # Convert cached dicts back to OptionResearch
    research_a = _dict_to_option_research(result.research_a)
    research_b = _dict_to_option_research(result.research_b)

    # Generate new criteria
    new_criteria = await go_deeper(
        option_a=result.option_a_name,
        option_b=result.option_b_name,
        intent=result.intent,
        existing_criteria=result.criteria,
        research_a=research_a,
        research_b=research_b,
    )

    # Append to existing criteria
    result.criteria.extend(new_criteria)
    storage.write_result(comparison_id, result)
    return result


@router.post("/comparisons/{comparison_id}/regenerate-weights")
async def regenerate_weights_endpoint(comparison_id: str):
    """Re-weight all criteria based on intent using AI."""
    result = storage.read_result(comparison_id)
    if not result:
        raise HTTPException(status_code=404, detail="Comparison not found")

    if not result.criteria:
        raise HTTPException(status_code=400, detail="No criteria to weight")

    # Get new weights from AI
    new_weights = await regenerate_weights(
        criteria=result.criteria,
        intent=result.intent,
    )

    # Apply new weights to each criterion
    for criterion in result.criteria:
        if criterion.id in new_weights:
            criterion.weight = new_weights[criterion.id]

    storage.write_result(comparison_id, result)
    return result


@router.get("/comparisons/{comparison_id}/flip-analysis")
async def get_flip_analysis(comparison_id: str):
    """Calculate flip analysis with sensitivity and actionable suggestions."""
    result = storage.read_result(comparison_id)
    if not result:
        raise HTTPException(status_code=404, detail="Comparison not found")

    if not result.criteria or not result.winner:
        return FlipAnalysisResponse(suggestions=[], sensitivity={})

    # Get current weights from criteria
    weights = {c.id: c.weight for c in result.criteria}

    # Calculate sensitivity for all criteria
    sensitivity = calculate_sensitivity(result.criteria, weights)

    # Calculate mathematical flip analysis
    flip_analysis = calculate_flip_analysis(result.criteria, weights, result.winner)

    # If we have cached research, generate actionable suggestions
    suggestions = []
    if result.research_a and result.research_b and flip_analysis:
        research_a = _dict_to_option_research(result.research_a)
        research_b = _dict_to_option_research(result.research_b)

        actionable = await generate_actionable_suggestions(
            option_a=result.option_a_name,
            option_b=result.option_b_name,
            winner=result.winner,
            flip_analysis=flip_analysis,
            research_a=research_a,
            research_b=research_b,
        )
        suggestions = [
            ActionableSuggestionModel(
                action=s.action,
                affected_criterion=s.affected_criterion,
                impact=s.impact,
                sources=s.sources,
            )
            for s in actionable
        ]

    return FlipAnalysisResponse(suggestions=suggestions, sensitivity=sensitivity)
