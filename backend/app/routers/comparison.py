from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uuid
from datetime import datetime
import time

from ..models import ComparisonInput, ComparisonResult, Criterion
from ..storage import JSONStorage

router = APIRouter(prefix="/api", tags=["comparison"])
storage = JSONStorage()


def generate_mock_result(comparison_id: str, data: ComparisonInput) -> None:
    """Simulate AI processing with mock criteria data."""
    time.sleep(1)  # Simulate processing delay

    mock_criteria = [
        Criterion(
            id="1",
            name="Environmental Impact",
            description="Overall environmental footprint including production and disposal",
            score_a=75,
            score_b=65,
            weight=50,
            sources=["https://example.com/env-study"],
        ),
        Criterion(
            id="2",
            name="Hidden Costs",
            description="Subsidies, externalities, and unaccounted expenses",
            score_a=60,
            score_b=70,
            weight=50,
            sources=["https://example.com/cost-analysis"],
        ),
        Criterion(
            id="3",
            name="Supply Chain Transparency",
            description="Visibility into sourcing and manufacturing practices",
            score_a=80,
            score_b=55,
            weight=50,
            sources=["https://example.com/supply-chain"],
        ),
    ]

    result = ComparisonResult(
        comparison_id=comparison_id,
        status="completed",
        option_a_name=data.option_a,
        option_b_name=data.option_b,
        intent=data.intent,
        criteria=mock_criteria,
        winner="a",
        reasoning=f"Based on your intent '{data.intent}', {data.option_a} scores higher overall.",
        created_at=datetime.now(),
        completed_at=datetime.now(),
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

    # Queue mock processing in background
    background_tasks.add_task(generate_mock_result, comparison_id, data)

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
    """List all saved comparison IDs."""
    return {"comparisons": storage.list_results()}
