"""Criteria service: Go Deeper and Regenerate Weights for N options."""

import json
import uuid
from pydantic import BaseModel, Field

from .config import get_anthropic_client
from .tavily_service import OptionResearch
from .usage_tracker import record_usage
from ..models import Criterion

_MODEL = "claude-sonnet-4-5-20250929"

_SYSTEM_BASE = {"type": "text", "text": "You are an expert at discovering non-obvious decision criteria."}
_SYSTEM_CACHED = {
    "type": "text",
    "text": "For Go Deeper: surface second-order effects, stakeholder perspectives, and systemic impacts not yet covered.",
    "cache_control": {"type": "ephemeral"},
}


class _AdditionalCriteria(BaseModel):
    criteria: list[dict] = Field(min_length=2, max_length=3)


class _WeightsOutput(BaseModel):
    weights: dict[str, float]


async def go_deeper(
    options: list[str],
    intent: str,
    research_by_option: dict[str, OptionResearch],
    existing_criteria: list[Criterion],
) -> list[Criterion]:
    """Generate 2-3 additional criteria using cached research."""
    client = get_anthropic_client()

    research_sections = []
    all_sources: set[str] = set()
    for opt in options:
        res = research_by_option.get(opt)
        if res and res.results:
            snippets = "\n\n".join(f"**{r.title}** ({r.url})\n{r.content}" for r in res.results)
            research_sections.append(f'RESEARCH FOR "{opt}":\n{snippets}')
            all_sources.update(r.url for r in res.results)

    existing_list = "\n".join(f"- {c.name}: {c.description}" for c in existing_criteria)
    options_str = ", ".join(f'"{o}"' for o in options)
    scores_template = ", ".join(f'"{o}": 75' for o in options)
    sources_list = "\n".join(sorted(all_sources)) or "(none)"

    prompt = (
        f"Generate 2-3 ADDITIONAL criteria for comparing {options_str}.\n"
        f"User intent: {intent}\n\n"
        f"Do NOT repeat:\n{existing_list}\n\n"
        + "\n\n".join(research_sections)
        + f"\n\nAVAILABLE SOURCE URLS:\n{sources_list}\n\n"
        f"Respond ONLY as JSON:\n"
        f'{{"criteria":[{{"name":"...","description":"...","scores":{{{scores_template}}},'
        f'"weight":30,"sources":["https://..."]}}]}}'
    )

    response = await client.messages.create(
        model=_MODEL,
        max_tokens=2048,
        system=[_SYSTEM_BASE, _SYSTEM_CACHED],
        messages=[{"role": "user", "content": prompt}],
    )
    record_usage("go_deeper", _MODEL, response.usage)

    content = response.content[0].text
    if "```json" in content:
        json_str = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        json_str = content.split("```")[1].split("```")[0].strip()
    else:
        json_str = content.strip()

    try:
        data = json.loads(json_str)
        output = _AdditionalCriteria.model_validate(data)
    except Exception as e:
        raise ValueError(f"Failed to parse go_deeper response: {e}")

    return [
        Criterion(
            id=str(uuid.uuid4()),
            name=c.get("name", ""),
            description=c.get("description", ""),
            scores=c.get("scores", {}),
            weight=c.get("weight", 50),
            sources=c.get("sources", []),
            origin="ai",
        )
        for c in output.criteria
    ]


async def regenerate_weights(
    criteria: list[Criterion],
    intent: str,
) -> dict[str, float]:
    """Ask AI to re-weight criteria by intent. Returns criterion_id → weight."""
    client = get_anthropic_client()

    criteria_list = "\n".join(f"- [{c.id}] {c.name}: {c.description}" for c in criteria)
    valid_ids = {c.id for c in criteria}

    prompt = (
        f"User intent: {intent}\n\n"
        f"Assign weights 0-100 to these criteria (roughly sum to 100):\n{criteria_list}\n\n"
        f'Respond ONLY as JSON: {{"weights": {{"<id>": 35, ...}}}}'
    )

    response = await client.messages.create(
        model=_MODEL,
        max_tokens=512,
        system=[
            {"type": "text", "text": "Assign weights reflecting the user's priorities."},
            {"type": "text", "text": "Use exact criterion IDs as keys.", "cache_control": {"type": "ephemeral"}},
        ],
        messages=[{"role": "user", "content": prompt}],
    )
    record_usage("regenerate_weights", _MODEL, response.usage)

    content = response.content[0].text
    if "```json" in content:
        json_str = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        json_str = content.split("```")[1].split("```")[0].strip()
    else:
        json_str = content.strip()

    try:
        data = json.loads(json_str)
        output = _WeightsOutput.model_validate(data)
    except Exception as e:
        raise ValueError(f"Failed to parse regenerate_weights response: {e}")

    result = {cid: w for cid, w in output.weights.items() if cid in valid_ids}
    for c in criteria:
        if c.id not in result:
            result[c.id] = 50.0
    return result
