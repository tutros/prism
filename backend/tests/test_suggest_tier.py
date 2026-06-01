"""
Integration tests for suggest_tier — require ANTHROPIC_API_KEY.
Skip automatically when key is not set.
"""
import os
import pytest
from app.services.suggest_tier import suggest_tier

pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)

VALID_TIERS = {"quick", "medium", "deep"}


def test_suggest_tier_returns_valid_tier():
    result = suggest_tier("Choosing a cloud database for a startup")
    assert result["tier"] in VALID_TIERS
    assert isinstance(result["rationale"], str)
    assert len(result["rationale"]) > 10


def test_suggest_tier_quick_for_simple_decision():
    result = suggest_tier("Should I use tabs or spaces?")
    assert result["tier"] in VALID_TIERS
    assert result["rationale"]


def test_suggest_tier_deep_for_complex_decision():
    result = suggest_tier(
        "Choosing an ERP system for a 500-person manufacturing company "
        "with compliance requirements in 3 countries"
    )
    assert result["tier"] in VALID_TIERS
    assert result["rationale"]
