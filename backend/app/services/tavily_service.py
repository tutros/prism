"""Tavily web search service for option research."""

import asyncio
from dataclasses import dataclass

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


async def search_option(option: str) -> OptionResearch:
    """Search for hidden costs and impacts of a single option.

    Query design follows Tavily best practices:
    - Specific focus on hidden costs, environmental impact, subsidies
    - max_results=10 for quality source diversity
    - search_depth="basic" for balanced speed/quality
    """
    try:
        tavily = get_tavily_client()

        # Query designed for non-obvious criteria discovery
        query = f"{option} hidden costs environmental impact subsidies externalities supply chain"

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

        return OptionResearch(option=option, results=results)

    except Exception as e:
        return OptionResearch(option=option, results=[], error=str(e))


async def search_both_options(option_a: str, option_b: str) -> tuple[OptionResearch, OptionResearch]:
    """Search for both options in parallel using asyncio.gather.

    Uses return_exceptions=True to handle partial failures gracefully.
    """
    results = await asyncio.gather(
        search_option(option_a),
        search_option(option_b),
        return_exceptions=True,
    )

    # Handle any exceptions from gather
    research_a = results[0] if not isinstance(results[0], Exception) else OptionResearch(
        option=option_a, results=[], error=str(results[0])
    )
    research_b = results[1] if not isinstance(results[1], Exception) else OptionResearch(
        option=option_b, results=[], error=str(results[1])
    )

    return research_a, research_b
