"""Orchestrator combining web search and AI analysis."""

from datetime import datetime

from ..models import ComparisonResult, Criterion
from .tavily_service import search_both_options
from .claude_service import generate_criteria
from .progress_store import add_progress, mark_complete


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
    )

    mark_complete(comparison_id)
    return result
