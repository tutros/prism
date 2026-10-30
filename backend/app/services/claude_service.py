"""Claude API service for criteria generation."""

import json
import re
from pydantic import BaseModel, Field

from .config import get_anthropic_client
from .source_quality import CLASSIFICATION_PROMPT, SourceClassification
from .tavily_service import OptionResearch
from .usage_tracker import record_usage

_MODEL = "claude-sonnet-4-5-20250929"

_SYSTEM_BASE = {
    "type": "text",
    "text": "You are an expert at generating decision criteria that surface non-obvious tradeoffs.",
}

_SYSTEM_CACHED = {
    "type": "text",
    "text": (
        "Generate 3-5 criteria per decision. For each criterion:\n"
        "- scores: dict keyed by option name (0-100, higher = better)\n"
        "- weight: importance to the user's intent (0-100)\n"
        "- winner: exact option name that scores highest overall\n"
        "Never hallucinate sources. Only cite URLs from the provided research."
    ),
    "cache_control": {"type": "ephemeral"},
}


class CriterionOutput(BaseModel):
    name: str
    description: str
    scores: dict[str, float] = Field(description="Keyed by option name, 0-100")
    weight: float = Field(ge=0, le=100)
    sources: list[str] = Field(default_factory=list)


class CriteriaOutput(BaseModel):
    criteria: list[CriterionOutput] = Field(min_length=3, max_length=5)
    winner: str = Field(description="Exact option name that wins")
    reasoning: str = Field(description="1-2 sentence plain-language explanation")
    source_classifications: list[SourceClassification] = Field(default_factory=list)


def _parse_criteria_output(text: str) -> CriteriaOutput:
    match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if match:
        json_str = match.group(1).strip()
    else:
        json_str = text.strip()
    try:
        return CriteriaOutput.model_validate(json.loads(json_str))
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse AI response as JSON: {e}")
    except Exception as e:
        raise ValueError(f"Failed to validate AI response: {e}")


async def generate_criteria_quick(options: list[str], intent: str) -> CriteriaOutput:
    """Quick tier: pure LLM knowledge, no web research."""
    client = get_anthropic_client()
    options_str = ", ".join(f'"{o}"' for o in options)
    scores_template = ", ".join(f'"{o}": 75' for o in options)
    prompt = (
        f"Compare these options: {options_str}\n"
        f"User intent: {intent}\n\n"
        f"Generate 3-5 criteria. Respond ONLY as JSON:\n"
        f'{{"criteria":[{{"name":"...","description":"...","scores":{{{scores_template}}},'
        f'"weight":50,"sources":[]}}],"winner":"{options[0]}","reasoning":"..."}}'
    )
    response = await client.messages.create(
        model=_MODEL,
        max_tokens=2048,
        system=[_SYSTEM_BASE, _SYSTEM_CACHED],
        messages=[{"role": "user", "content": prompt}],
    )
    record_usage("criteria_quick", _MODEL, response.usage)
    return _parse_criteria_output(response.content[0].text)


async def generate_criteria_medium(
    options: list[str],
    intent: str,
    research_by_option: dict[str, OptionResearch],
) -> CriteriaOutput:
    """Medium/Deep tier: uses Tavily research context."""
    client = get_anthropic_client()

    research_sections = []
    all_sources: set[str] = set()
    for opt in options:
        res = research_by_option.get(opt)
        if res and res.results:
            snippets = "\n\n".join(f"**{r.title}** ({r.url})\n{r.content}" for r in res.results)
            research_sections.append(f'RESEARCH FOR "{opt}":\n{snippets}')
            all_sources.update(r.url for r in res.results)
        else:
            research_sections.append(f'RESEARCH FOR "{opt}":\nNo results found.')

    options_str = ", ".join(f'"{o}"' for o in options)
    scores_template = ", ".join(f'"{o}": 75' for o in options)
    sources_list = "\n".join(sorted(all_sources)) or "(none)"

    prompt = (
        f"Compare these options: {options_str}\n"
        f"User intent: {intent}\n\n"
        + "\n\n".join(research_sections)
        + f"\n\nAVAILABLE SOURCE URLS (only use these):\n{sources_list}\n\n"
        f"Generate 3-5 non-obvious criteria. Each criterion must cite at least one source URL from above.\n"
        + CLASSIFICATION_PROMPT
        + f"\nRespond ONLY as JSON:\n"
        f'{{"criteria":[{{"name":"...","description":"...","scores":{{{scores_template}}},'
        f'"weight":50,"sources":["https://..."]}}],"winner":"{options[0]}","reasoning":"...",'
        f'"source_classifications":[{{"url":"https://...","quality":"news"}}]}}'
    )
    response = await client.messages.create(
        model=_MODEL,
        max_tokens=4096,
        system=[_SYSTEM_BASE, _SYSTEM_CACHED],
        messages=[{"role": "user", "content": prompt}],
    )
    record_usage("criteria_medium", _MODEL, response.usage)
    return _parse_criteria_output(response.content[0].text)
