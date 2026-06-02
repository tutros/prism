"""
Router integration tests. Tests 1-5 require no API keys.
Tests 6-7 require ANTHROPIC_API_KEY and are skipped automatically without it.
"""
import os
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.models import Decision, AnalysisResult, Criterion
from app.storage import JSONStorage

UTC = timezone.utc
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


def _decision():
    return Decision(
        id=DECISION_ID,
        title="Choosing a cloud database",
        options=["PostgreSQL", "MongoDB", "PlanetScale"],
        option_contexts={},
        intent="Best 5-year cost",
        created_at=datetime(2026, 6, 1, 12, 0, 0, tzinfo=UTC),
    )


def _analysis(status="completed"):
    return AnalysisResult(
        analysis_id=ANALYSIS_ID,
        decision_id=DECISION_ID,
        tier="quick",
        status=status,
        options=["PostgreSQL", "MongoDB", "PlanetScale"],
        winner="PostgreSQL",
        reasoning="PostgreSQL leads on cost.",
        criteria=[
            Criterion(
                id="c1",
                name="Cost",
                description="TCO",
                scores={"PostgreSQL": 80.0, "MongoDB": 60.0, "PlanetScale": 70.0},
                weight=50.0,
            )
        ],
        weights_original={"Cost": 0.5},
        weights_current={"Cost": 0.5},
        created_at=datetime(2026, 6, 1, 12, 0, 0, tzinfo=UTC),
        completed_at=datetime(2026, 6, 1, 12, 0, 5, tzinfo=UTC),
    )


# ── 1. Tracer bullet ─────────────────────────────────────────────────────────

def test_list_decisions_empty(client):
    resp = client.get("/api/decisions")
    assert resp.status_code == 200
    assert resp.json() == {"decisions": []}


# ── 2. GET analysis → 404 ────────────────────────────────────────────────────

def test_get_analysis_not_found(client):
    resp = client.get(f"/api/decisions/{DECISION_ID}/analyses/{ANALYSIS_ID}")
    assert resp.status_code == 404


# ── 3. GET analysis → 200 ────────────────────────────────────────────────────

def test_get_analysis_found(client, storage):
    storage.write_decision(_decision())
    storage.write_analysis(_analysis())
    resp = client.get(f"/api/decisions/{DECISION_ID}/analyses/{ANALYSIS_ID}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["analysis_id"] == ANALYSIS_ID
    assert body["winner"] == "PostgreSQL"
    assert body["status"] == "completed"


# ── 4. PATCH weights → updates weights_current ───────────────────────────────

def test_patch_weights_updates_storage(client, storage):
    storage.write_decision(_decision())
    storage.write_analysis(_analysis())

    new_weights = {"Cost": 0.8}
    resp = client.patch(
        f"/api/decisions/{DECISION_ID}/analyses/{ANALYSIS_ID}/weights",
        json={"weights_current": new_weights},
    )
    assert resp.status_code == 200
    assert resp.json()["weights_current"] == new_weights

    # Verify persisted
    updated = storage.read_analysis(DECISION_ID, ANALYSIS_ID)
    assert updated.weights_current == new_weights


# ── 5. Dedup key ─────────────────────────────────────────────────────────────

def test_dedup_key_same_inputs_same_hash():
    from app.routers.comparison import _dedup_key
    h1 = _dedup_key(["PostgreSQL", "MongoDB"], "5-year cost", "quick")
    h2 = _dedup_key(["MongoDB", "PostgreSQL"], "5-year cost", "quick")  # order shouldn't matter
    assert h1 == h2


def test_dedup_key_different_tier_different_hash():
    from app.routers.comparison import _dedup_key
    h1 = _dedup_key(["PostgreSQL", "MongoDB"], "5-year cost", "quick")
    h2 = _dedup_key(["PostgreSQL", "MongoDB"], "5-year cost", "medium")
    assert h1 != h2


# ── 6. POST /api/decisions (requires API key) ─────────────────────────────────

@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
def test_create_decision_returns_tier_suggestion(client):
    resp = client.post("/api/decisions", json={
        "options": ["PostgreSQL", "MongoDB"],
        "intent": "Best database for a 3-person startup",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert "decision_id" in body
    assert body["suggested_tier"] in ("quick", "medium", "deep")
    assert body["rationale"]
