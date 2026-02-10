"""Criteria service for Go Deeper and Regenerate Weights features."""

import json
from pydantic import BaseModel, Field

from .config import get_anthropic_client
from .tavily_service import OptionResearch
from ..models import Criterion


class AdditionalCriterionOutput(BaseModel):
    """Single additional criterion from Go Deeper."""
    name: str = Field(description="Short name for the criterion")
    description: str = Field(description="Explanation of why this criterion matters")
    score_a: float = Field(ge=0, le=100, description="Score for option A (0-100)")
    score_b: float = Field(ge=0, le=100, description="Score for option B (0-100)")
    weight: float = Field(ge=0, le=100, description="Importance weight (0-100)")
    sources: list[str] = Field(description="Source URLs from research")


class AdditionalCriteriaOutput(BaseModel):
    """Output from Go Deeper request."""
    criteria: list[AdditionalCriterionOutput] = Field(min_length=2, max_length=3)


class WeightsOutput(BaseModel):
    """Output from Regenerate Weights request."""
    weights: dict[str, float] = Field(description="Mapping of criterion name to weight 0-100")


async def go_deeper(
    option_a: str,
    option_b: str,
    intent: str,
    existing_criteria: list[Criterion],
    research_a: OptionResearch,
    research_b: OptionResearch,
) -> list[Criterion]:
    """Generate 2-3 additional criteria using cached research.

    Uses same Claude model and patterns as the initial criteria generation,
    but explicitly excludes existing criteria to get new perspectives.
    """
    client = get_anthropic_client()

    # Format research into readable context
    context_a = "\n\n".join([
        f"**{r.title}** ({r.url})\n{r.content}"
        for r in research_a.results
    ]) if research_a.results else "No research results found."

    context_b = "\n\n".join([
        f"**{r.title}** ({r.url})\n{r.content}"
        for r in research_b.results
    ]) if research_b.results else "No research results found."

    # Collect all source URLs for citation validation
    all_sources = {r.url for r in research_a.results} | {r.url for r in research_b.results}

    # Build exclusion list from existing criteria
    existing_list = "\n".join([
        f"- {c.name}: {c.description}"
        for c in existing_criteria
    ])

    prompt = f"""Generate 2-3 ADDITIONAL non-obvious criteria for comparing "{option_a}" vs "{option_b}".

USER INTENT: {intent}

IMPORTANT: Do NOT repeat these existing criteria:
{existing_list}

Generate NEW criteria that explore:
- Second-order effects not covered above
- Different stakeholder perspectives (workers, communities, future generations)
- Long-term vs short-term tradeoffs
- Regional or contextual variations
- Systemic impacts and feedback loops

CRITICAL RULES:
1. Focus on HIDDEN COSTS - things people don't normally consider
2. Each criterion MUST include at least one source URL from the research below
3. Only use URLs that appear in the research - do not make up URLs
4. Score both options 0-100 based on the research
5. Weight based on user's stated intent

RESEARCH FOR "{option_a}":
{context_a}

RESEARCH FOR "{option_b}":
{context_b}

AVAILABLE SOURCE URLS (only use these):
{chr(10).join(sorted(all_sources))}

RESPOND WITH ONLY A JSON OBJECT in this exact format:
{{
  "criteria": [
    {{
      "name": "Criterion Name",
      "description": "Why this matters",
      "score_a": 75,
      "score_b": 60,
      "weight": 30,
      "sources": ["https://example.com/source"]
    }}
  ]
}}

Do not include any text before or after the JSON."""

    response = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": "You are an expert at discovering non-obvious decision criteria that surface hidden costs and systemic impacts.",
            },
            {
                "type": "text",
                "text": """Your role is to help people see the invisible threads connecting everyday choices to larger systems.

For Go Deeper requests, focus on perspectives not yet covered:
- Infrastructure dependencies and lock-in effects
- Social and cultural impacts
- Opportunity costs and alternatives
- Risk profiles and uncertainty

Always ground your analysis in the provided research. Never hallucinate facts or sources.""",
                "cache_control": {"type": "ephemeral"}
            }
        ],
        messages=[{"role": "user", "content": prompt}],
    )

    # Parse response
    content = response.content[0].text

    # Find JSON in the response
    if "```json" in content:
        json_str = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        json_str = content.split("```")[1].split("```")[0].strip()
    else:
        json_str = content.strip()

    try:
        data = json.loads(json_str)
        output = AdditionalCriteriaOutput.model_validate(data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse AI response as JSON: {str(e)}")
    except Exception as e:
        raise ValueError(f"Failed to validate AI response: {str(e)}")

    # Convert to Criterion objects with unique IDs
    import uuid
    new_criteria = [
        Criterion(
            id=str(uuid.uuid4()),
            name=c.name,
            description=c.description,
            score_a=c.score_a,
            score_b=c.score_b,
            weight=c.weight,
            sources=c.sources,
            origin="ai",
        )
        for c in output.criteria
    ]

    return new_criteria


async def regenerate_weights(
    criteria: list[Criterion],
    intent: str,
) -> dict[str, float]:
    """Ask AI to re-weight all criteria based on intent.

    Returns dict mapping criterion_id -> new_weight.
    All criteria (AI and user) are included in the analysis.
    """
    client = get_anthropic_client()

    # Build criteria list with names for Claude to reference
    criteria_list = "\n".join([
        f"- {c.name}: {c.description}"
        for c in criteria
    ])

    # Build name-to-id mapping for response translation
    name_to_id = {c.name: c.id for c in criteria}

    prompt = f"""Given these criteria for a comparison, assign weights (0-100) based on the user's intent.

USER INTENT: {intent}

CRITERIA TO WEIGHT:
{criteria_list}

RULES:
1. Weights should reflect relative importance to the user's stated intent
2. Weights should approximately sum to 100 (we normalize after)
3. All criteria should receive a weight (including any custom user-added ones)
4. Higher weight = more important for this user's decision

RESPOND WITH ONLY A JSON OBJECT in this exact format:
{{
  "weights": {{
    "Criterion Name 1": 35,
    "Criterion Name 2": 25,
    "Criterion Name 3": 40
  }}
}}

Use the exact criterion names from the list above as keys.
Do not include any text before or after the JSON."""

    response = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": "You are an expert at weighting decision criteria based on user intent and priorities.",
            },
            {
                "type": "text",
                "text": """Assign weights that:
- Prioritize criteria most relevant to the user's stated goals
- Balance between immediate and long-term considerations
- Consider the relative magnitude of impact for each criterion

Be thoughtful about what the user actually cares about based on their intent statement.""",
                "cache_control": {"type": "ephemeral"}
            }
        ],
        messages=[{"role": "user", "content": prompt}],
    )

    # Parse response
    content = response.content[0].text

    # Find JSON in the response
    if "```json" in content:
        json_str = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        json_str = content.split("```")[1].split("```")[0].strip()
    else:
        json_str = content.strip()

    try:
        data = json.loads(json_str)
        output = WeightsOutput.model_validate(data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse AI response as JSON: {str(e)}")
    except Exception as e:
        raise ValueError(f"Failed to validate AI response: {str(e)}")

    # Translate names to IDs
    result = {}
    for name, weight in output.weights.items():
        if name in name_to_id:
            result[name_to_id[name]] = weight

    # If any criteria were missed, assign default weight
    for c in criteria:
        if c.id not in result:
            result[c.id] = 50.0  # Default fallback

    return result
