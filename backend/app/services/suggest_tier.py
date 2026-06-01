"""Lightweight tier auto-suggestion using claude-haiku."""
import json
import asyncio
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


async def _suggest_tier_async(decision_text: str) -> TierSuggestion:
    client = get_anthropic_client()
    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        system=_SYSTEM,
        messages=[{"role": "user", "content": decision_text}],
    )
    data = json.loads(response.content[0].text)
    return TierSuggestion(tier=data["tier"], rationale=data["rationale"])


def suggest_tier(decision_text: str) -> TierSuggestion:
    """Synchronous wrapper — call from FastAPI using asyncio.run or await the async version."""
    return asyncio.run(_suggest_tier_async(decision_text))
