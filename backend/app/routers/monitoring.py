"""Developer monitoring endpoint for token usage and cost tracking."""

from fastapi import APIRouter

from ..services.usage_tracker import get_usage_stats
from ..services.spending_guard import get_daily_spend
from ..services.tavily_service import get_cache_stats

router = APIRouter(prefix="/api", tags=["monitoring"])


@router.get("/monitoring")
async def get_monitoring():
    """Developer dashboard: token usage, costs, cache stats."""
    usage = get_usage_stats()
    daily = get_daily_spend()
    cache = get_cache_stats()

    return {
        "today": daily,
        "usage": usage,
        "cache": cache,
    }
