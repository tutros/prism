"""
Criterion confidence (#14): source classification + the source-quality rule.
No API keys needed; Claude and Tavily are mocked.
"""
import asyncio
import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import AnalysisResult, Criterion, Decision
from app.services import llm
from app.services.source_quality import (
    SourceClassification,
    classify_sources,
    compute_confidence,
)
from app.services.tavily_service import OptionResearch, SearchResult
from app.storage import JSONStorage

UTC = timezone.utc
GOV = "https://energy.gov/report"
PEER = "https://nature.com/study"
IND = "https://industry.org/whitepaper"
NEWS = "https://news.com/story"
BLOG = "https://someblog.net/post"
QUALITY = {GOV: "government", PEER: "peer-reviewed", IND: "industry", NEWS: "news", BLOG: "blog"}


# ── compute_confidence: one test per level ───────────────────────────────────

def test_high_needs_two_sources_and_one_peer_reviewed_or_government():
    assert compute_confidence([GOV, BLOG], QUALITY) == "high"
    assert compute_confidence([PEER, NEWS], QUALITY) == "high"


def test_medium_needs_one_industry_or_news_source():
    assert compute_confidence([IND], QUALITY) == "medium"
    assert compute_confidence([NEWS, BLOG], QUALITY) == "medium"


def test_low_when_only_blog_sources():
    assert compute_confidence([BLOG], QUALITY) == "low"


# ── compute_confidence: edge cases ───────────────────────────────────────────

def test_single_government_source_is_medium_not_high():
    # >=1 source with a quality above blog, but not the 2 sources high needs
    assert compute_confidence([GOV], QUALITY) == "medium"


def test_zero_sources_is_low():
    assert compute_confidence([], QUALITY) == "low"


def test_sources_with_no_classification_are_low():
    quality = {GOV: "unknown", NEWS: "unknown"}
    assert compute_confidence([GOV, NEWS], quality) == "low"


def test_urls_not_in_the_research_are_ignored():
    # The hallucinated URL must not supply the second source high needs
    assert compute_confidence([GOV, "https://made-up.example/x"], QUALITY) == "medium"
    assert compute_confidence(["https://made-up.example/x"], QUALITY) == "low"


def test_duplicate_urls_count_once():
    assert compute_confidence([GOV, GOV], QUALITY) == "medium"


# ── classify_sources ─────────────────────────────────────────────────────────

def test_classify_sources_keeps_research_urls_and_defaults_to_unknown():
    research_urls = {GOV, NEWS, BLOG}
    labels = [
        SourceClassification(url=GOV, quality="government"),
        SourceClassification(url=NEWS, quality="tabloid"),  # not a valid tier
        SourceClassification(url="https://made-up.example/x", quality="peer-reviewed"),
    ]
    assert classify_sources(labels, research_urls) == {
        GOV: "government",
        NEWS: "unknown",
        BLOG: "unknown",
    }


# ── Claude output parsing ────────────────────────────────────────────────────

def test_criteria_output_parses_source_classifications():
    from app.services.claude_service import _parse_criteria_output
    raw = json.dumps({
        "criteria": [
            {"name": n, "description": "d", "scores": {"A": 50}, "weight": 50, "sources": [GOV]}
            for n in ("One", "Two", "Three")
        ],
        "winner": "A",
        "reasoning": "r",
        "source_classifications": [{"url": GOV, "quality": "government"}],
    })
    out = _parse_criteria_output(raw)
    assert out.source_classifications == [SourceClassification(url=GOV, quality="government")]


def test_criteria_output_without_classifications_defaults_to_empty():
    from app.services.claude_service import _parse_criteria_output
    raw = json.dumps({
        "criteria": [
            {"name": n, "description": "d", "scores": {"A": 50}, "weight": 50}
            for n in ("One", "Two", "Three")
        ],
        "winner": "A",
        "reasoning": "r",
    })
    assert _parse_criteria_output(raw).source_classifications == []


class _FakeMessages:
    def __init__(self, text):
        self.text = text
        self.prompt = None

    async def create(self, **kwargs):
        self.prompt = kwargs["messages"][0]["content"]
        return SimpleNamespace(
            content=[SimpleNamespace(text=self.text)],
            usage=SimpleNamespace(input_tokens=1, output_tokens=1,
                                  cache_creation_input_tokens=0, cache_read_input_tokens=0),
        )


def _fake_client(monkeypatch, text):
    messages = _FakeMessages(text)
    monkeypatch.delenv("LLM_BACKEND", raising=False)
    monkeypatch.setattr(llm, "get_anthropic_client", lambda: SimpleNamespace(messages=messages))
    monkeypatch.setattr(llm, "record_usage", lambda *a, **k: None)
    return messages


def _research(urls_by_option):
    return {
        opt: OptionResearch(
            option=opt,
            results=[SearchResult(title="t", url=u, content="c", score=1.0) for u in urls],
        )
        for opt, urls in urls_by_option.items()
    }


def test_medium_prompt_asks_claude_to_classify_each_source(monkeypatch):
    from app.services import claude_service
    raw = json.dumps({
        "criteria": [
            {"name": n, "description": "d", "scores": {"A": 50, "B": 50}, "weight": 50, "sources": [GOV]}
            for n in ("One", "Two", "Three")
        ],
        "winner": "A",
        "reasoning": "r",
        "source_classifications": [{"url": GOV, "quality": "government"}],
    })
    messages = _fake_client(monkeypatch, raw)
    asyncio.run(claude_service.generate_criteria_medium(["A", "B"], "intent", _research({"A": [GOV], "B": []})))
    for tier in ("peer-reviewed", "government", "industry", "news", "blog", "source_classifications"):
        assert tier in messages.prompt


# ── Orchestrator ─────────────────────────────────────────────────────────────

def _criteria_output(sources_per_criterion, classifications=()):
    from app.services.claude_service import CriteriaOutput, CriterionOutput
    return CriteriaOutput(
        criteria=[
            CriterionOutput(name=f"C{i}", description="d", scores={"A": 60, "B": 40}, weight=50, sources=s)
            for i, s in enumerate(sources_per_criterion)
        ],
        winner="A",
        reasoning="r",
        source_classifications=list(classifications),
    )


def test_medium_tier_grades_criteria_and_stores_classification(monkeypatch):
    from app.services import orchestrator

    async def mock_search(options, force_refresh=False):
        return _research({"A": [GOV, PEER, NEWS], "B": [BLOG]})

    async def mock_generate(options, intent, research_by_option):
        return _criteria_output(
            [[GOV, PEER], [NEWS], [BLOG]],
            [SourceClassification(url=u, quality=q) for u, q in QUALITY.items()],
        )

    monkeypatch.setattr(orchestrator, "search_all_options", mock_search)
    monkeypatch.setattr(orchestrator, "generate_criteria_medium", mock_generate)

    result = asyncio.run(orchestrator.run_analysis("a1", "d1", ["A", "B"], "intent", "medium"))

    assert [c.confidence for c in result.criteria] == ["high", "medium", "low"]
    # Only URLs from the research are stored; IND was never researched
    assert result.source_quality == {GOV: "government", PEER: "peer-reviewed", NEWS: "news", BLOG: "blog"}


def test_quick_tier_criteria_are_not_graded(monkeypatch):
    from app.services import orchestrator

    async def mock_quick(options, intent):
        return _criteria_output([[], [], []])

    monkeypatch.setattr(orchestrator, "generate_criteria_quick", mock_quick)

    result = asyncio.run(orchestrator.run_analysis("a1", "d1", ["A", "B"], "intent", "quick"))

    assert result.status == "completed"
    assert all(c.confidence is None for c in result.criteria)
    assert result.source_quality == {}


# ── Router: go-deeper and user-added criteria ────────────────────────────────

DECISION_ID = "550e8400-e29b-41d4-a716-446655440000"
ANALYSIS_ID = "660e8400-e29b-41d4-a716-446655440001"


@pytest.fixture
def storage(tmp_path):
    return JSONStorage(data_dir=str(tmp_path))


@pytest.fixture
def client(storage, monkeypatch):
    import app.routers.comparison as comp_module
    monkeypatch.setattr(comp_module, "storage", storage)
    with TestClient(app) as c:
        yield c


def _seed(storage, tier="medium"):
    from dataclasses import asdict
    now = datetime(2026, 6, 1, 12, 0, 0, tzinfo=UTC)
    storage.write_decision(Decision(
        id=DECISION_ID, title="t", options=["A", "B"], intent="intent", created_at=now,
    ))
    research = {o: asdict(r) for o, r in _research({"A": [GOV, PEER], "B": [NEWS]}).items()}
    storage.write_analysis(AnalysisResult(
        analysis_id=ANALYSIS_ID, decision_id=DECISION_ID, tier=tier, status="completed",
        options=["A", "B"], winner="A",
        criteria=[Criterion(id="c1", name="Cost", description="d", scores={"A": 60, "B": 40},
                            sources=[GOV], confidence="medium")],
        research=research if tier != "quick" else {},
        source_quality={GOV: "government"} if tier != "quick" else {},
        created_at=now, completed_at=now,
    ))


def test_go_deeper_criteria_are_graded_by_the_same_rule(client, storage, monkeypatch):
    from app.services import criteria_service
    _seed(storage)
    raw = json.dumps({
        "criteria": [
            {"name": "Policy risk", "description": "d", "scores": {"A": 50, "B": 70}, "weight": 30,
             "sources": [GOV, PEER]},
            {"name": "Coverage", "description": "d", "scores": {"A": 50, "B": 70}, "weight": 30,
             "sources": [NEWS]},
        ],
        "source_classifications": [
            {"url": PEER, "quality": "peer-reviewed"},
            {"url": NEWS, "quality": "news"},
        ],
    })
    messages = _fake_client(monkeypatch, raw)

    resp = client.post(f"/api/decisions/{DECISION_ID}/analyses/{ANALYSIS_ID}/go-deeper")

    assert resp.status_code == 200
    assert "source_classifications" in messages.prompt
    body = resp.json()
    new = {c["name"]: c["confidence"] for c in body["criteria"][1:]}
    # GOV was classified in the original run; the merge keeps it
    assert new == {"Policy risk": "high", "Coverage": "medium"}
    assert body["source_quality"] == {GOV: "government", PEER: "peer-reviewed", NEWS: "news"}


def test_user_added_criteria_are_not_graded(client, storage):
    _seed(storage)
    resp = client.post(
        f"/api/decisions/{DECISION_ID}/analyses/{ANALYSIS_ID}/criteria",
        json={"name": "Gut feel", "description": "Mine", "scores": {"A": 90, "B": 10}},
    )
    assert resp.status_code == 201
    assert resp.json()["confidence"] is None


def test_malformed_source_labels_do_not_fail_the_output():
    from app.services.claude_service import _parse_criteria_output
    raw = json.dumps({
        "criteria": [
            {"name": n, "description": "d", "scores": {"A": 50}, "weight": 50, "sources": [GOV]}
            for n in ("One", "Two", "Three")
        ],
        "winner": "A",
        "reasoning": "r",
        "source_classifications": [
            {"url": GOV, "quality": None},
            {"url": NEWS},
            {"quality": "news"},
            "not-an-object",
            {"url": PEER, "quality": "peer-reviewed"},
        ],
    })
    out = _parse_criteria_output(raw)
    assert classify_sources(out.source_classifications, {GOV, NEWS, PEER}) == {
        GOV: "unknown", NEWS: "unknown", PEER: "peer-reviewed",
    }


def test_go_deeper_on_analysis_saved_before_grading(client, storage, monkeypatch):
    from app.services import criteria_service
    _seed(storage)
    # Strip the new field and the old default grade, as in pre-#14 JSON files
    stored = storage.read_analysis(DECISION_ID, ANALYSIS_ID).model_dump(mode="json")
    stored.pop("source_quality")
    stored["criteria"][0]["confidence"] = "low"
    storage.write_analysis(AnalysisResult.model_validate(stored))
    raw = json.dumps({
        "criteria": [
            {"name": "Policy risk", "description": "d", "scores": {"A": 50, "B": 70}, "weight": 30,
             "sources": [GOV, PEER]},
            {"name": "Coverage", "description": "d", "scores": {"A": 50, "B": 70}, "weight": 30,
             "sources": [NEWS]},
        ],
        "source_classifications": [
            {"url": GOV, "quality": "government"},
            {"url": NEWS, "quality": "news"},
        ],
    })
    _fake_client(monkeypatch, raw)

    resp = client.post(f"/api/decisions/{DECISION_ID}/analyses/{ANALYSIS_ID}/go-deeper")

    assert resp.status_code == 200
    body = resp.json()
    assert body["criteria"][0]["confidence"] == "low"  # old grade left as stored
    assert {c["name"]: c["confidence"] for c in body["criteria"][1:]} == {
        "Policy risk": "high", "Coverage": "medium",
    }
    assert body["source_quality"] == {GOV: "government", PEER: "unknown", NEWS: "news"}
