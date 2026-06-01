import pytest
from datetime import datetime, timezone
from app.models import Decision, AnalysisResult, Criterion, HiddenProperty
from app.storage import JSONStorage

UTC = timezone.utc

DECISION_ID = "550e8400-e29b-41d4-a716-446655440000"
ANALYSIS_ID = "660e8400-e29b-41d4-a716-446655440001"


def make_decision(id: str = DECISION_ID) -> Decision:
    return Decision(
        id=id,
        title="Choosing a cloud database",
        options=["PostgreSQL", "MongoDB", "PlanetScale"],
        option_contexts={"PostgreSQL": "Open source, ACID compliant"},
        intent="Best 5-year cost with a 3-person dev team",
        created_at=datetime(2026, 6, 1, 12, 0, 0, tzinfo=UTC),
    )


def make_analysis(decision_id: str = DECISION_ID, analysis_id: str = ANALYSIS_ID) -> AnalysisResult:
    criterion = Criterion(
        id="c1",
        name="Cost",
        description="Total cost of ownership",
        scores={"PostgreSQL": 80.0, "MongoDB": 60.0, "PlanetScale": 70.0},
        weight=50.0,
        sources=["https://example.com"],
        origin="ai",
        confidence="high",
    )
    return AnalysisResult(
        analysis_id=analysis_id,
        decision_id=decision_id,
        tier="quick",
        status="completed",
        options=["PostgreSQL", "MongoDB", "PlanetScale"],
        winner="PostgreSQL",
        reasoning="PostgreSQL leads on cost and maturity.",
        criteria=[criterion],
        weights_original={"Cost": 0.5},
        weights_current={"Cost": 0.5},
        research={},
        hidden_properties=[],
        created_at=datetime(2026, 6, 1, 12, 0, 0, tzinfo=UTC),
        completed_at=datetime(2026, 6, 1, 12, 0, 5, tzinfo=UTC),
    )


def test_decision_roundtrip(tmp_path):
    storage = JSONStorage(data_dir=str(tmp_path))
    decision = make_decision()
    storage.write_decision(decision)
    result = storage.read_decision(decision.id)
    assert result == decision


def test_analysis_roundtrip(tmp_path):
    storage = JSONStorage(data_dir=str(tmp_path))
    storage.write_decision(make_decision())
    analysis = make_analysis()
    storage.write_analysis(analysis)
    result = storage.read_analysis(DECISION_ID, ANALYSIS_ID)
    assert result == analysis


def test_list_decisions(tmp_path):
    storage = JSONStorage(data_dir=str(tmp_path))
    id1 = "550e8400-e29b-41d4-a716-446655440000"
    id2 = "660e8400-e29b-41d4-a716-446655440001"
    storage.write_decision(make_decision(id=id1))
    storage.write_decision(make_decision(id=id2))
    assert set(storage.list_decisions()) == {id1, id2}


def test_list_analyses(tmp_path):
    storage = JSONStorage(data_dir=str(tmp_path))
    storage.write_decision(make_decision())
    aid1 = "660e8400-e29b-41d4-a716-446655440001"
    aid2 = "770e8400-e29b-41d4-a716-446655440002"
    storage.write_analysis(make_analysis(analysis_id=aid1))
    storage.write_analysis(make_analysis(analysis_id=aid2))
    assert set(storage.list_analyses(DECISION_ID)) == {aid1, aid2}


def test_invalid_decision_id_rejected(tmp_path):
    storage = JSONStorage(data_dir=str(tmp_path))
    with pytest.raises(ValueError):
        storage.read_decision("../evil")


def test_invalid_analysis_id_rejected(tmp_path):
    storage = JSONStorage(data_dir=str(tmp_path))
    with pytest.raises(ValueError):
        storage.read_analysis(DECISION_ID, "not-a-uuid")


def test_read_missing_decision_returns_none(tmp_path):
    storage = JSONStorage(data_dir=str(tmp_path))
    assert storage.read_decision(DECISION_ID) is None


def test_read_missing_analysis_returns_none(tmp_path):
    storage = JSONStorage(data_dir=str(tmp_path))
    assert storage.read_analysis(DECISION_ID, ANALYSIS_ID) is None
