"""Orchestrator: routes analysis to Quick / Medium / Deep pipeline."""

import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Literal

from ..models import AnalysisResult, Criterion
from .tavily_service import search_all_options, OptionResearch
from .claude_service import generate_criteria_quick, generate_criteria_medium
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

    # Deep tier: hidden properties (Phase 4 — no-op for now)
    hidden_properties = []
    if tier == "deep":
        add_progress(analysis_id, "Discovering hidden properties...")
        # Phase 4 wires hidden_service here

    # Build criteria with generated IDs
    criteria = [
        Criterion(
            id=str(i + 1),
            name=c.name,
            description=c.description,
            scores=c.scores,
            weight=c.weight,
            sources=c.sources,
            origin="ai",
            confidence="low",
        )
        for i, c in enumerate(output.criteria)
    ]

    # Weights derived from criteria weight fields (normalised to sum 1.0)
    total = sum(c.weight for c in criteria) or 1.0
    weights = {c.name: round(c.weight / total, 4) for c in criteria}

    # Research stored as plain dicts for JSON serialisation
    research_store: dict = {}
    if tier != "quick":
        research_store = {
            opt: asdict(res) for opt, res in research_by_option.items()
        }

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
        hidden_properties=hidden_properties,
        created_at=now,
        completed_at=datetime.now(timezone.utc),
    )
