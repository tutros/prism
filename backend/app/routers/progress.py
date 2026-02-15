"""Server-Sent Events endpoint for progress streaming."""

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from typing import AsyncGenerator

from ..services.progress_store import progress_store, progress_complete, cleanup

router = APIRouter(prefix="/api", tags=["progress"])


async def progress_generator(comparison_id: str) -> AsyncGenerator[dict, None]:
    """Generate SSE events for a comparison's progress."""
    last_index = 0
    max_wait = 120  # 2 minute timeout
    waited = 0

    while waited < max_wait:
        # Check for new messages
        messages = progress_store.get(comparison_id, [])
        while last_index < len(messages):
            yield {
                "event": "progress",
                "data": json.dumps({"status": messages[last_index]})
            }
            last_index += 1

        # Check if complete
        if progress_complete.get(comparison_id):
            yield {
                "event": "complete",
                "data": json.dumps({"comparison_id": comparison_id})
            }
            cleanup(comparison_id)
            return

        # Wait and poll again
        await asyncio.sleep(0.5)
        waited += 0.5

    # Timeout
    cleanup(comparison_id)
    yield {
        "event": "error",
        "data": json.dumps({"error": "Progress stream timed out"})
    }


@router.get("/progress/{comparison_id}")
async def stream_progress(comparison_id: str):
    """Stream progress updates for a comparison via SSE."""
    return EventSourceResponse(progress_generator(comparison_id))
