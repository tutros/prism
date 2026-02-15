"""Flip detection service for sensitivity analysis and actionable suggestions."""

import json
from pydantic import BaseModel, Field

from .config import get_anthropic_client
from .tavily_service import OptionResearch
from .usage_tracker import record_usage
from ..models import Criterion


class FlipSuggestion(BaseModel):
    """Mathematical flip suggestion from sensitivity analysis."""
    criterion_id: str
    criterion_name: str
    current_weight: float
    required_weight_increase: float
    sensitivity_score: float


class ActionableSuggestion(BaseModel):
    """User-facing actionable suggestion with sources."""
    action: str
    affected_criterion: str
    impact: str
    sources: list[str] = []


class ActionableSuggestionsOutput(BaseModel):
    """Structured output from Claude."""
    suggestions: list[ActionableSuggestion] = Field(min_length=1, max_length=3)


def calculate_sensitivity(
    criteria: list[Criterion],
    weights: dict[str, float]
) -> dict[str, float]:
    """Calculate sensitivity score for each criterion.

    Sensitivity = |score_a - score_b| * normalized_weight
    Higher = this criterion has more influence on the outcome
    """
    total_weight = sum(weights.values())
    if total_weight == 0:
        return {}

    sensitivities = {}
    for c in criteria:
        w = weights.get(c.id, c.weight) / total_weight
        score_diff = abs(c.score_a - c.score_b)
        sensitivities[c.id] = round(score_diff * w, 3)

    # Normalize to 0-1 range
    max_sens = max(sensitivities.values()) if sensitivities else 1
    if max_sens == 0:
        return {k: 0.0 for k in sensitivities}

    return {k: round(v / max_sens, 3) for k, v in sensitivities.items()}


def calculate_flip_analysis(
    criteria: list[Criterion],
    weights: dict[str, float],
    winner: str
) -> list[FlipSuggestion]:
    """Calculate what weight changes would flip the winner.

    Returns top 3 most feasible flip scenarios.
    """
    total_weight = sum(weights.values())
    if total_weight == 0:
        return []

    # Calculate current scores
    score_a = sum(
        c.score_a * weights.get(c.id, c.weight) / total_weight
        for c in criteria
    )
    score_b = sum(
        c.score_b * weights.get(c.id, c.weight) / total_weight
        for c in criteria
    )

    gap = abs(score_a - score_b)
    if gap < 0.01:  # Essentially tied
        return []

    loser = 'a' if winner == 'b' else 'b'
    sensitivities = calculate_sensitivity(criteria, weights)
    suggestions = []

    for c in criteria:
        # Does this criterion favor the loser?
        loser_score = c.score_a if loser == 'a' else c.score_b
        winner_score = c.score_b if loser == 'a' else c.score_a

        if loser_score <= winner_score:
            continue  # Can't help by increasing this weight

        advantage = loser_score - winner_score
        current_w = weights.get(c.id, c.weight)

        # Calculate required weight increase
        # Simplified approximation for small changes
        required_increase = (gap / advantage) * total_weight

        # Only show realistic changes (not more than doubling the weight)
        if required_increase > 0 and required_increase <= current_w * 2:
            suggestions.append(FlipSuggestion(
                criterion_id=c.id,
                criterion_name=c.name,
                current_weight=current_w,
                required_weight_increase=round(required_increase, 1),
                sensitivity_score=sensitivities.get(c.id, 0.5)
            ))

    # Sort by feasibility (smallest change first)
    suggestions.sort(key=lambda s: s.required_weight_increase)
    return suggestions[:3]


async def generate_actionable_suggestions(
    option_a: str,
    option_b: str,
    winner: str,
    flip_analysis: list[FlipSuggestion],
    research_a: OptionResearch,
    research_b: OptionResearch,
) -> list[ActionableSuggestion]:
    """Transform mathematical flip analysis into actionable user suggestions.

    Uses Claude to generate realistic suggestions grounded in research sources.
    """
    if not flip_analysis:
        return []

    client = get_anthropic_client()

    loser = option_a if winner == 'b' else option_b
    winner_name = option_b if winner == 'b' else option_a

    # Format research into readable context
    context_a = "\n\n".join([
        f"**{r.title}** ({r.url})\n{r.content}"
        for r in research_a.results[:5]  # Limit to top 5
    ]) if research_a.results else "No research found."

    context_b = "\n\n".join([
        f"**{r.title}** ({r.url})\n{r.content}"
        for r in research_b.results[:5]
    ]) if research_b.results else "No research found."

    # Collect source URLs
    all_sources = {r.url for r in research_a.results} | {r.url for r in research_b.results}

    # Format flip analysis
    flip_text = "\n".join([
        f"- {s.criterion_name}: increasing weight by {s.required_weight_increase}% would help flip outcome"
        for s in flip_analysis
    ])

    prompt = f"""Based on the flip analysis below, generate 2-3 ACTIONABLE suggestions for how "{loser}" could become the better choice instead of "{winner_name}".

FLIP ANALYSIS (mathematical):
{flip_text}

RESEARCH FOR "{option_a}":
{context_a}

RESEARCH FOR "{option_b}":
{context_b}

AVAILABLE SOURCE URLS (only use these):
{chr(10).join(sorted(all_sources))}

RULES FOR SUGGESTIONS:
1. Must be REALISTIC actions the user could take or conditions that could apply
2. Must reference at least one source URL from the research
3. Do NOT suggest impossible changes like:
   - "Change government policy"
   - "If the product were completely different"
   - "If laws were different"
   - "If prices were different"
4. DO suggest things like:
   - "If you [specific user action], then..."
   - "In regions with [specific condition], ..."
   - "If you plan to [usage pattern], ..."
   - "For households that [specific characteristic], ..."

RESPOND WITH ONLY A JSON OBJECT in this exact format:
{{
  "suggestions": [
    {{
      "action": "If you have access to local glass recycling...",
      "affected_criterion": "Recycling Infrastructure",
      "impact": "This increases the importance of recycling infrastructure, shifting the balance toward glass",
      "sources": ["https://example.com/source"]
    }}
  ]
}}

Do not include any text before or after the JSON."""

    try:
        response = await client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1500,
            system=[
                {
                    "type": "text",
                    "text": "You are an expert at transforming mathematical analysis into practical, actionable advice.",
                },
                {
                    "type": "text",
                    "text": """Your role is to help users understand what real-world actions or conditions would change their decision outcome.

Focus on:
- User behaviors they can change
- Environmental conditions they should consider
- Usage patterns that affect the comparison
- Regional or contextual factors

Always ground suggestions in the research sources provided. Never suggest impossible changes.""",
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            messages=[{"role": "user", "content": prompt}],
        )
        record_usage("flip_suggestions", "claude-sonnet-4-5-20250929", response.usage)

        # Parse response - safely extract text content
        if not response.content or not hasattr(response.content[0], 'text'):
            raise ValueError("Claude returned an empty or non-text response")
        content = response.content[0].text

        # Find JSON in the response
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0].strip()
        else:
            json_str = content.strip()

        data = json.loads(json_str)
        output = ActionableSuggestionsOutput.model_validate(data)
        return output.suggestions

    except Exception as e:
        # Fallback: return basic suggestions without AI
        return [
            ActionableSuggestion(
                action=f"Consider prioritizing {s.criterion_name} more highly in your decision",
                affected_criterion=s.criterion_name,
                impact=f"Increasing focus on this criterion by {s.required_weight_increase}% could change the outcome",
                sources=[]
            )
            for s in flip_analysis[:2]
        ]
