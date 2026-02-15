"""Developer monitoring endpoint for token usage and cost tracking."""

import os

from fastapi import APIRouter, HTTPException

from ..services.usage_tracker import get_usage_stats
from ..services.spending_guard import get_daily_spend
from ..services.tavily_service import get_cache_stats

router = APIRouter(prefix="/api", tags=["monitoring"])


@router.get("/monitoring")
async def get_monitoring():
    """Developer dashboard: token usage, costs, cache stats.

    Disabled when MONITORING_ENABLED=false (defaults to enabled for dev).
    """
    if os.environ.get("MONITORING_ENABLED", "true").lower() == "false":
        raise HTTPException(status_code=404, detail="Not found")

    usage = get_usage_stats()
    daily = get_daily_spend()
    cache = get_cache_stats()

    return {
        "today": daily,
        "usage": usage,
        "cache": cache,
    }
