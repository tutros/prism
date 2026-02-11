"""Orchestrator combining web search and AI analysis."""

from dataclasses import asdict
from datetime import datetime
from typing import Literal

from ..models import ComparisonResult, Criterion, SourceMetadata
from .tavily_service import search_both_options
from .claude_service import generate_criteria, SourceClassification
from .progress_store import add_progress, mark_complete

# Quality tiers ordered from highest to lowest trust
_QUALITY_RANK: dict[str, int] = {
    "peer-reviewed": 4,
    "government": 3,
    "industry": 2,
    "news": 1,
    "blog": 0,
    "unknown": 0,
}


def compute_confidence(
    sources: list[str],
    source_metadata: dict[str, SourceMetadata],
) -> Literal["high", "medium", "low"]:
    """Compute confidence level for a criterion based on its source quality and count.

    Rules:
    - high:   >= 2 sources AND at least one peer-reviewed or government source
    - medium: >= 1 source AND at least one industry or news source (no peer-reviewed/gov)
    - low:    0 sources, or only blog/unknown sources
    """
    if not sources:
        return "low"

    qualities = [source_metadata.get(url, SourceMetadata()).quality for url in sources]
    max_rank = max(_QUALITY_RANK.get(q, 0) for q in qualities)

    if len(sources) >= 2 and max_rank >= 3:  # peer-reviewed or government
        return "high"
    if len(sources) >= 1 and max_rank >= 1:  # industry or news
        return "medium"
    return "low"


async def generate_comparison(
    comparison_id: str,
    option_a: str,
    option_b: str,
    intent: str,
) -> ComparisonResult:
    """Orchestrate full comparison with progress updates.

    Flow:
    1. Search web for both options in parallel (Tavily)
    2. Generate criteria from research (Claude)
    3. Package into ComparisonResult
    """

    # Step 1: Parallel web search
    add_progress(comparison_id, f"Searching web for {option_a}...")
    add_progress(comparison_id, f"Searching web for {option_b}...")

    research_a, research_b = await search_both_options(option_a, option_b)

    add_progress(comparison_id, f"Found {len(research_a.results)} sources for {option_a}")
    add_progress(comparison_id, f"Found {len(research_b.results)} sources for {option_b}")

    # Check for complete search failure
    if research_a.error and research_b.error:
        mark_complete(comparison_id)
        return ComparisonResult(
            comparison_id=comparison_id,
            status="error",
            option_a_name=option_a,
            option_b_name=option_b,
            intent=intent,
            criteria=[],
            winner=None,
            reasoning=f"Web search failed: {research_a.error}",
            created_at=datetime.now(),
            completed_at=datetime.now(),
        )

    # Step 2: Generate criteria via Claude
    add_progress(comparison_id, "Analyzing sources for hidden costs...")

    try:
        criteria_output = await generate_criteria(
            option_a=option_a,
            option_b=option_b,
            intent=intent,
            research_a=research_a,
            research_b=research_b,
        )
    except Exception as e:
        mark_complete(comparison_id)
        return ComparisonResult(
            comparison_id=comparison_id,
            status="error",
            option_a_name=option_a,
            option_b_name=option_b,
            intent=intent,
            criteria=[],
            winner=None,
            reasoning=f"AI analysis failed: {str(e)}",
            created_at=datetime.now(),
            completed_at=datetime.now(),
        )

    add_progress(comparison_id, f"Generated {len(criteria_output.criteria)} criteria")

    # Step 3: Package result
    add_progress(comparison_id, "Finalizing comparison...")

    # Build source_metadata from Claude's classifications
    valid_qualities = {"peer-reviewed", "government", "industry", "news", "blog", "unknown"}
    source_metadata: dict[str, SourceMetadata] = {
        sc.url: SourceMetadata(
            quality=sc.quality if sc.quality in valid_qualities else "unknown"
        )
        for sc in criteria_output.source_classifications
    }

    criteria = [
        Criterion(
            id=str(i + 1),
            name=c.name,
            description=c.description,
            score_a=c.score_a,
            score_b=c.score_b,
            weight=c.weight,
            sources=c.sources,
            origin="ai",
            confidence=compute_confidence(c.sources, source_metadata),
        )
        for i, c in enumerate(criteria_output.criteria)
    ]

    result = ComparisonResult(
        comparison_id=comparison_id,
        status="completed",
        option_a_name=option_a,
        option_b_name=option_b,
        intent=intent,
        criteria=criteria,
        winner=criteria_output.winner,
        reasoning=criteria_output.reasoning,
        created_at=datetime.now(),
        completed_at=datetime.now(),
        research_a=asdict(research_a),
        research_b=asdict(research_b),
        source_metadata=source_metadata,
    )

    mark_complete(comparison_id)
    return result
