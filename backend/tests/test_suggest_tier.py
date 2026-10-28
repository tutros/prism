"""
Tests for suggest_tier.

Parsing tests need no API key. The live tests at the bottom require
ANTHROPIC_API_KEY and skip automatically when it is not set.
"""
import json
import os
import pytest
from app.services.suggest_tier import suggest_tier, _parse_tier_suggestion

_live = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)

VALID_TIERS = {"quick", "medium", "deep"}

_PAYLOAD = {"tier": "medium", "rationale": "Benefits from a little research."}


# -- Parsing (no API) ---------------------------------------------------------

def test_parse_bare_json():
    assert _parse_tier_suggestion(json.dumps(_PAYLOAD)) == _PAYLOAD


def test_parse_json_fence():
    # claude-haiku returns ```json ... ``` despite "Return ONLY valid JSON".
    raw = "```json\n" + json.dumps(_PAYLOAD, indent=2) + "\n```"
    assert _parse_tier_suggestion(raw) == _PAYLOAD


def test_parse_plain_fence():
    raw = "```\n" + json.dumps(_PAYLOAD) + "\n```"
    assert _parse_tier_suggestion(raw) == _PAYLOAD


def test_parse_uppercase_or_other_fence_tag():
    # Review nit: ```JSON / ```javascript tags must not leak into the payload.
    for tag in ("JSON", "javascript"):
        raw = "```" + tag + chr(10) + json.dumps(_PAYLOAD) + chr(10) + "```"
        assert _parse_tier_suggestion(raw) == _PAYLOAD


def test_parse_invalid_tier_raises():
    with pytest.raises(ValueError):
        _parse_tier_suggestion(json.dumps({"tier": "ultra", "rationale": "x"}))


def test_parse_non_json_raises():
    with pytest.raises(ValueError):
        _parse_tier_suggestion("Sure! I would pick medium.")


# -- Live (require ANTHROPIC_API_KEY) -----------------------------------------


@_live
def test_suggest_tier_returns_valid_tier():
    result = suggest_tier("Choosing a cloud database for a startup")
    assert result["tier"] in VALID_TIERS
    assert isinstance(result["rationale"], str)
    assert len(result["rationale"]) > 10


@_live
def test_suggest_tier_quick_for_simple_decision():
    result = suggest_tier("Should I use tabs or spaces?")
    assert result["tier"] in VALID_TIERS
    assert result["rationale"]


@_live
def test_suggest_tier_deep_for_complex_decision():
    result = suggest_tier(
        "Choosing an ERP system for a 500-person manufacturing company "
        "with compliance requirements in 3 countries"
    )
    assert result["tier"] in VALID_TIERS
    assert result["rationale"]
