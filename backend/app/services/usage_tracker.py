"""Token usage tracking for Claude API calls."""

import json
import os
import tempfile
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


# Price per token for claude-sonnet-4-5-20250929 (in USD)
PRICE_PER_TOKEN: dict[str, dict[str, float]] = {
    "claude-sonnet-4-5-20250929": {
        "input": 3.00 / 1_000_000,
        "cache_write": 3.75 / 1_000_000,
        "cache_read": 0.30 / 1_000_000,
        "output": 15.00 / 1_000_000,
    }
}

# Absolute path to data/ directory (backend/data/)
_DATA_DIR = Path(__file__).parent.parent.parent / "data"
_METRICS_FILE = _DATA_DIR / "usage_metrics.json"


@dataclass
class UsageRecord:
    """Single Claude API call usage record."""
    feature: str
    model: str
    input_tokens: int
    output_tokens: int
    cache_creation_tokens: int
    cache_read_tokens: int
    cost_usd: float
    timestamp: str


_usage_records: list[dict] = []
_lock = threading.Lock()


def calculate_cost(model: str, usage) -> float:
    """Calculate cost in USD from a Claude API usage object."""
    prices = PRICE_PER_TOKEN.get(model, PRICE_PER_TOKEN["claude-sonnet-4-5-20250929"])
    cost = (
        (usage.input_tokens * prices["input"])
        + ((getattr(usage, "cache_creation_input_tokens", None) or 0) * prices["cache_write"])
        + ((getattr(usage, "cache_read_input_tokens", None) or 0) * prices["cache_read"])
        + (usage.output_tokens * prices["output"])
    )
    return round(cost, 8)


def _persist_records(records: list[dict]) -> None:
    """Atomically write usage records to disk."""
    _DATA_DIR.mkdir(exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=_DATA_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as tmp:
            json.dump(records, tmp, indent=2)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_path, _METRICS_FILE)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def record_usage(feature: str, model: str, usage) -> UsageRecord:
    """Record a Claude API call's token usage and persist to disk.

    Also accumulates daily spend in spending_guard.
    """
    from .spending_guard import add_cost  # avoid circular import at module level

    cost = calculate_cost(model, usage)
    record = UsageRecord(
        feature=feature,
        model=model,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", None) or 0,
        cache_read_tokens=getattr(usage, "cache_read_input_tokens", None) or 0,
        cost_usd=cost,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    with _lock:
        _usage_records.append(asdict(record))
        try:
            _persist_records(list(_usage_records))
        except Exception:
            pass  # Never fail the API call because of metrics persistence

        # Add cost inside lock to prevent TOCTOU race with spending guard
        add_cost(cost)

    return record


def get_usage_stats() -> dict:
    """Return aggregated usage statistics."""
    with _lock:
        records = list(_usage_records)

    total_input = 0
    total_output = 0
    total_cache_read = 0
    total_cache_creation = 0
    total_cost = 0.0
    by_feature: dict[str, dict] = {}

    for r in records:
        total_input += r.get("input_tokens", 0)
        total_output += r.get("output_tokens", 0)
        total_cache_read += r.get("cache_read_tokens", 0)
        total_cache_creation += r.get("cache_creation_tokens", 0)
        total_cost += r.get("cost_usd", 0.0)

        feature = r.get("feature", "unknown")
        if feature not in by_feature:
            by_feature[feature] = {"count": 0, "cost_usd": 0.0}
        by_feature[feature]["count"] += 1
        by_feature[feature]["cost_usd"] = round(
            by_feature[feature]["cost_usd"] + r.get("cost_usd", 0.0), 8
        )

    return {
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_cache_read_tokens": total_cache_read,
        "total_cache_creation_tokens": total_cache_creation,
        "total_cost_usd": round(total_cost, 8),
        "by_feature": by_feature,
    }


def _load_records_from_disk() -> None:
    """Load persisted usage records on module startup."""
    global _usage_records
    if _METRICS_FILE.exists():
        try:
            data = json.loads(_METRICS_FILE.read_text())
            if isinstance(data, list):
                _usage_records = data
        except Exception:
            pass  # Start fresh if file is corrupt


# Load persisted records on module import
_load_records_from_disk()
