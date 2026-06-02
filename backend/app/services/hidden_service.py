"""Hidden property discovery for the Deep analysis tier."""

import json
from typing import Any

from .config import get_anthropic_client
from .usage_tracker import record_usage
from ..models import HiddenProperty

_MODEL = "claude-sonnet-4-5-20250929"

_SYSTEM = (
    "You are a hidden cost and benefit analyst. Uncover properties of decisions "
    "that are NOT immediately obvious to the decision-maker.\n\n"
    "For each option, examine ALL of these flow categories simultaneously:\n"
    "- money: subsidies, tax implications, opportunity costs, hidden fees, maintenance, depreciation\n"
    "- energy: consumption, generation, efficiency, carbon credits, renewable incentives\n"
    "- materials: supply chain dependencies, scarcity, recycling potential, waste\n"
    "- labor: employment impacts, training requirements, productivity, health and safety\n"
    "- environmental: carbon emissions, pollution, ecosystem impact, water usage, compliance costs\n"
    "- political: regulatory risk, lobbying dynamics, vendor lock-in, policy change exposure\n\n"
    "Focus on properties that are:\n"
    "- Not commonly discussed or immediately visible\n"
    "- Often overlooked by decision-makers\n"
    "- Potentially significant — systemic or second-order effects\n\n"
    "Return ONLY valid JSON: "
    '{"properties": [{"name": "...", "category": "money|energy|materials|labor|environmental|political", '
    '"magnitude": "High|Medium|Low", "confidence": "high|medium|low", "description": "..."}]}'
)


def _parse_hidden_properties(text: str) -> list[HiddenProperty]:
    if "```json" in text:
        json_str = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        json_str = text.split("```")[1].split("```")[0].strip()
    else:
        json_str = text.strip()
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse hidden properties response as JSON: {e}")
    return [
        HiddenProperty(
            name=p["name"],
            category=p["category"],
            magnitude=p["magnitude"],
            confidence=p["confidence"],
            description=p["description"],
        )
        for p in data.get("properties", [])
    ]


async def discover_hidden_properties(
    options: list[str],
    intent: str,
    research: dict[str, Any],
) -> list[HiddenProperty]:
    """Discover hidden systemic properties across all options (Deep tier)."""
    client = get_anthropic_client()

    options_str = ", ".join(f'"{o}"' for o in options)
    research_sections = []
    for opt in options:
        res = research.get(opt, {})
        results = res.get("results", []) if isinstance(res, dict) else []
        if results:
            snippets = "\n".join(
                f"- {r.get('title', '')} ({r.get('url', '')}): {r.get('content', '')[:200]}"
                for r in results[:3]
            )
            research_sections.append(f'RESEARCH FOR "{opt}":\n{snippets}')

    research_context = "\n\n".join(research_sections) or "(No web research available)"
    prompt = (
        f"Decision: {intent}\n"
        f"Options being compared: {options_str}\n\n"
        f"{research_context}\n\n"
        f"Discover 3-6 hidden properties that apply across these options — "
        f"systemic costs, externalities, and second-order effects not captured in standard criteria. "
        f"Each property should be non-obvious and potentially decision-changing."
    )

    response = await client.messages.create(
        model=_MODEL,
        max_tokens=2048,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    record_usage("hidden_properties", _MODEL, response.usage)
    return _parse_hidden_properties(response.content[0].text)
