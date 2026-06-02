"""Tavily web search service for option research."""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

from cachetools import TTLCache

from .config import get_tavily_client


@dataclass
class SearchResult:
    """Single search result with source info."""
    title: str
    url: str
    content: str
    score: float


@dataclass
class OptionResearch:
    """Research results for a single option."""
    option: str
    results: list[SearchResult]
    error: str | None = None
    cached_at: str | None = None  # ISO timestamp if from cache


# In-memory cache for Tavily results: 200 entries max, 24h TTL
_TAVILY_CACHE: TTLCache = TTLCache(maxsize=200, ttl=86400)
_CACHE_LOCK = asyncio.Lock()


async def search_option(option: str, force_refresh: bool = False) -> OptionResearch:
    """Search for hidden costs and impacts of a single option.

    Query design follows Tavily best practices:
    - Specific focus on hidden costs, environmental impact, subsidies
    - max_results=10 for quality source diversity
    - search_depth="basic" for balanced speed/quality

    Results are cached in-memory for 24h. Pass force_refresh=True to bypass cache.
    """
    # Query designed for non-obvious criteria discovery
    query = f"{option} hidden costs environmental impact subsidies externalities supply chain"
    cache_key = query.lower().strip()

    # Check cache unless force_refresh requested
    if not force_refresh:
        async with _CACHE_LOCK:
            cached = _TAVILY_CACHE.get(cache_key)
        if cached is not None:
            results, cached_at = cached
            return OptionResearch(option=option, results=results, cached_at=cached_at)

    try:
        tavily = get_tavily_client()

        response = await tavily.search(
            query=query,
            search_depth="basic",
            max_results=10,
        )

        results = [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                content=r.get("content", ""),
                score=r.get("score", 0.0),
            )
            for r in response.get("results", [])
        ]

        # Store in cache
        now_iso = datetime.now(timezone.utc).isoformat()
        async with _CACHE_LOCK:
            _TAVILY_CACHE[cache_key] = (results, now_iso)

        return OptionResearch(option=option, results=results)

    except Exception as e:
        return OptionResearch(option=option, results=[], error=str(e))


def get_cache_stats() -> dict:
    """Return Tavily cache statistics."""
    return {
        "tavily_entries": len(_TAVILY_CACHE),
        "tavily_maxsize": _TAVILY_CACHE.maxsize,
    }


async def search_all_options(
    options: list[str], force_refresh: bool = False
) -> dict[str, OptionResearch]:
    """Search for all options in parallel. Returns dict keyed by option name."""
    raw = await asyncio.gather(
        *[search_option(opt, force_refresh=force_refresh) for opt in options],
        return_exceptions=True,
    )
    return {
        opt: (r if not isinstance(r, Exception) else OptionResearch(option=opt, results=[], error=str(r)))
        for opt, r in zip(options, raw)
    }
