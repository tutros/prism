from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uuid
from datetime import datetime

from ..models import ComparisonInput, ComparisonResult, Criterion
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
