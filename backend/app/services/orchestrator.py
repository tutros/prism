"""Orchestrator: routes analysis to Quick / Medium / Deep pipeline."""

import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Literal

from ..models import AnalysisResult, Criterion
from .tavily_service import search_all_options, OptionResearch
from .claude_service import generate_criteria_quick, generate_criteria_medium
from .hidden_service import discover_hidden_properties
from .source_quality import classify_sources, compute_confidence
from .progress_store import add_progress, mark_complete


async def run_analysis(
    analysis_id: str,
    decision_id: str,
    options: list[str],
    intent: str,
    tier: Literal["quick", "medium", "deep"],
    option_contexts: dict[str, str] | None = None,
) -> AnalysisResult:
    """Run the full analysis pipeline for the given tier."""
    now = datetime.now(timezone.utc)

    if tier == "quick":
        add_progress(analysis_id, "Generating criteria (Quick — no web search)...")
        try:
            output = await generate_criteria_quick(options, intent)
        except Exception as e:
            mark_complete(analysis_id)
            return AnalysisResult(
                analysis_id=analysis_id,
                decision_id=decision_id,
                tier=tier,
                status="error",
                options=options,
                reasoning=f"AI analysis failed: {e}",
                created_at=now,
                completed_at=datetime.now(timezone.utc),
            )
        add_progress(analysis_id, f"Generated {len(output.criteria)} criteria")

    else:  # medium or deep
        for opt in options:
            add_progress(analysis_id, f"Searching web for {opt}...")
        research_by_option = await search_all_options(options)

        for opt, res in research_by_option.items():
            add_progress(analysis_id, f"Found {len(res.results)} sources for {opt}")

        add_progress(analysis_id, "Analyzing research...")
        try:
            output = await generate_criteria_medium(options, intent, research_by_option)
        except Exception as e:
            mark_complete(analysis_id)
            return AnalysisResult(
                analysis_id=analysis_id,
                decision_id=decision_id,
                tier=tier,
                status="error",
                options=options,
                reasoning=f"AI analysis failed: {e}",
                created_at=now,
                completed_at=datetime.now(timezone.utc),
            )
        add_progress(analysis_id, f"Generated {len(output.criteria)} criteria")

    # Serialise research for JSON storage (empty for Quick tier)
    research_store: dict = {}
    source_quality: dict[str, str] = {}
    if tier != "quick":
        research_store = {
            opt: asdict(res) for opt, res in research_by_option.items()
        }
        research_urls = {r.url for res in research_by_option.values() for r in res.results}
        source_quality = classify_sources(output.source_classifications, research_urls)

    # Deep tier: hidden properties
    hidden_properties = []
    if tier == "deep":
        add_progress(analysis_id, "Discovering hidden properties...")
        try:
            hidden_properties = await discover_hidden_properties(
                options=options,
                intent=intent,
                research=research_store,
            )
        except Exception:
            pass  # hidden properties are best-effort; don't fail the analysis

    # Build criteria with generated IDs
    criteria = [
        Criterion(
            id=str(uuid.uuid4()),
            name=c.name,
            description=c.description,
            scores=c.scores,
            weight=c.weight,
            sources=c.sources,
            origin="ai",
            # Quick tier has no sources, so its criteria are not graded
            confidence=None if tier == "quick" else compute_confidence(c.sources, source_quality),
        )
        for i, c in enumerate(output.criteria)
    ]

    # Weights derived from criteria weight fields (normalised to sum 1.0)
    total = sum(c.weight for c in criteria) or 1.0
    weights = {c.name: round(c.weight / total, 4) for c in criteria}

    add_progress(analysis_id, "Finalizing...")
    mark_complete(analysis_id)

    return AnalysisResult(
        analysis_id=analysis_id,
        decision_id=decision_id,
        tier=tier,
        status="completed",
        options=options,
        winner=output.winner,
        reasoning=output.reasoning,
        criteria=criteria,
        weights_original=weights,
        weights_current=weights,
        research=research_store,
        source_quality=source_quality,
        hidden_properties=hidden_properties,
        created_at=now,
        completed_at=datetime.now(timezone.utc),
    )
