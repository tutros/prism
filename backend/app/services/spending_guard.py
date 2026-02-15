"""Daily spending cap guard for Claude API costs."""

import json
import os
import threading
from datetime import date
from pathlib import Path


_DAILY_CAP_USD = float(os.environ.get("DAILY_SPEND_CAP_USD", "5.0"))

_today: str = date.today().isoformat()
_daily_cost_usd: float = 0.0
_lock = threading.Lock()


def _load_today_cost() -> None:
    """Load today's accumulated cost from persisted usage records on startup."""
    global _today, _daily_cost_usd
    metrics_file = Path(__file__).parent.parent.parent / "data" / "usage_metrics.json"
    _today = date.today().isoformat()
    if not metrics_file.exists():
        return
    try:
        records = json.loads(metrics_file.read_text())
        if isinstance(records, list):
            for r in records:
                if r.get("timestamp", "").startswith(_today):
                    _daily_cost_usd += r.get("cost_usd", 0.0)
    except Exception:
        pass  # Start fresh if file is corrupt


_load_today_cost()


def _reset_if_new_day() -> None:
    """Reset daily counter if day has changed. Must be called under lock."""
    global _today, _daily_cost_usd
    today = date.today().isoformat()
    if today != _today:
        _today = today
        _daily_cost_usd = 0.0


def check_spending_cap() -> None:
    """Raise ValueError if daily spending cap has been reached."""
    with _lock:
        _reset_if_new_day()
        if _daily_cost_usd >= _DAILY_CAP_USD:
            raise ValueError(
                f"Daily spending cap of ${_DAILY_CAP_USD:.2f} reached "
                f"(spent ${_daily_cost_usd:.4f} today). "
                "Try again tomorrow or increase DAILY_SPEND_CAP_USD."
            )


def add_cost(cost: float) -> None:
    """Add cost to the daily accumulator."""
    global _daily_cost_usd
    with _lock:
        _reset_if_new_day()
        _daily_cost_usd += cost


def get_daily_spend() -> dict:
    """Return current daily spend status."""
    with _lock:
        _reset_if_new_day()
        return {
            "cost_usd": _daily_cost_usd,
            "cap_usd": _DAILY_CAP_USD,
            "date": _today,
        }
