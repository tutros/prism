"""Lightweight tier auto-suggestion using claude-haiku."""
import json
import asyncio
import re
from typing import Literal, TypedDict

from .config import get_anthropic_client

_SYSTEM = """You are a routing assistant for a decision analysis tool.
Given a decision description, classify it into one of three depth tiers:
- quick: simple, low-stakes, or purely personal decisions (seconds matter)
- medium: moderately complex decisions that benefit from web research
- deep: high-stakes, irreversible, or complex systemic decisions

Return ONLY valid JSON: {"tier": "quick"|"medium"|"deep", "rationale": "<one sentence>"}"""


class TierSuggestion(TypedDict):
    tier: Literal["quick", "medium", "deep"]
    rationale: str


_VALID_TIERS = {"quick", "medium", "deep"}
_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```")


def _parse_tier_suggestion(text: str) -> TierSuggestion:
    """Parse the model reply into a TierSuggestion.

    Haiku wraps its reply in a ```json fence despite being told not to, so the
    fence is stripped before parsing (same approach as claude_service).
    """
    match = _FENCE_RE.search(text)
    json_str = match.group(1).strip() if match else text.strip()
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Tier suggestion was not valid JSON: {e}") from e
    tier = data.get("tier") if isinstance(data, dict) else None
    if tier not in _VALID_TIERS:
        raise ValueError(f"Tier suggestion returned unknown tier: {tier!r}")
    return TierSuggestion(tier=tier, rationale=str(data.get("rationale", "")))


async def _suggest_tier_async(decision_text: str) -> TierSuggestion:
    client = get_anthropic_client()
    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        system=_SYSTEM,
        messages=[{"role": "user", "content": decision_text}],
    )
    return _parse_tier_suggestion(response.content[0].text)


def suggest_tier(decision_text: str) -> TierSuggestion:
    """Synchronous wrapper — call from FastAPI using asyncio.run or await the async version."""
    return asyncio.run(_suggest_tier_async(decision_text))
