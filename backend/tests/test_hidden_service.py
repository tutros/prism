"""
Tests for hidden_service (Phase 4 — Deep tier).
All parsing tests require no API keys.
The orchestrator integration test monkeypatches discover_hidden_properties.
"""
import asyncio
import json
import pytest

from app.models import HiddenProperty


# ── 1. Tracer bullet: parse valid JSON → list[HiddenProperty] ────────────────

def test_parse_returns_hidden_properties():
    from app.services.hidden_service import _parse_hidden_properties
    raw = json.dumps({"properties": [
        {
            "name": "Vendor Lock-in Cost",
            "category": "money",
            "magnitude": "High",
            "confidence": "medium",
            "description": "Switching away incurs significant migration costs.",
        }
    ]})
    props = _parse_hidden_properties(raw)
    assert len(props) == 1
    assert isinstance(props[0], HiddenProperty)
    assert props[0].name == "Vendor Lock-in Cost"
    assert props[0].magnitude == "High"
    assert props[0].confidence == "medium"


# ── 2. JSON wrapped in markdown fences ──────────────────────────────────────

def test_parse_handles_json_fence():
    from app.services.hidden_service import _parse_hidden_properties
    raw = (
        "```json\n"
        + json.dumps({"properties": [
            {"name": "P", "category": "energy", "magnitude": "Low", "confidence": "low", "description": "d"}
        ]})
        + "\n```"
    )
    props = _parse_hidden_properties(raw)
    assert len(props) == 1
    assert props[0].category == "energy"


# ── 3. Bad JSON raises ValueError ────────────────────────────────────────────

def test_parse_invalid_json_raises():
    from app.services.hidden_service import _parse_hidden_properties
    with pytest.raises(ValueError):
        _parse_hidden_properties("not json at all")


# ── 4. Orchestrator deep tier wires discover_hidden_properties ───────────────

def test_deep_tier_includes_hidden_properties(monkeypatch):
    from app.services import orchestrator
    from app.services.claude_service import CriteriaOutput, CriterionOutput
    from app.services.tavily_service import OptionResearch

    stub_hp = HiddenProperty(
        name="Lock-in Risk",
        category="money",
        magnitude="High",
        confidence="high",
        description="Significant switching cost if vendor changes pricing.",
    )

    async def mock_search(options, force_refresh=False):
        return {o: OptionResearch(option=o, results=[]) for o in options}

    async def mock_generate_medium(options, intent, research_by_option):
        return CriteriaOutput(
            criteria=[
                CriterionOutput(name="Cost", description="TCO", scores={o: 75.0 for o in options}, weight=50, sources=[]),
                CriterionOutput(name="Speed", description="Query speed", scores={o: 70.0 for o in options}, weight=30, sources=[]),
                CriterionOutput(name="Ease", description="Setup ease", scores={o: 80.0 for o in options}, weight=20, sources=[]),
            ],
            winner=options[0],
            reasoning="A is best overall.",
        )

    async def mock_discover(options, intent, research):
        return [stub_hp]

    monkeypatch.setattr(orchestrator, "search_all_options", mock_search)
    monkeypatch.setattr(orchestrator, "generate_criteria_medium", mock_generate_medium)
    monkeypatch.setattr(orchestrator, "discover_hidden_properties", mock_discover)

    result = asyncio.run(orchestrator.run_analysis(
        analysis_id="a1",
        decision_id="d1",
        options=["A", "B"],
        intent="Pick the best option",
        tier="deep",
    ))

    assert result.status == "completed"
    assert len(result.hidden_properties) == 1
    assert result.hidden_properties[0].name == "Lock-in Risk"
