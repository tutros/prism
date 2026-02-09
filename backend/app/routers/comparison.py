from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uuid
from datetime import datetime

from ..models import ComparisonInput, ComparisonResult, Criterion, CriterionCreate, CriterionUpdate
from ..storage import JSONStorage
from ..services.orchestrator import generate_comparison

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
