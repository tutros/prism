"""Shared progress tracking store.

This module is imported by both orchestrator.py and routers/progress.py.
Keeping it in services/ avoids circular import issues.
"""

# In-memory progress store (comparison_id -> list of status messages)
# For POC; production would use Redis or similar
progress_store: dict[str, list[str]] = {}
progress_complete: dict[str, bool] = {}


def add_progress(comparison_id: str, status: str) -> None:
    """Add a progress message for a comparison."""
    if comparison_id not in progress_store:
        progress_store[comparison_id] = []
    progress_store[comparison_id].append(status)


def mark_complete(comparison_id: str) -> None:
    """Mark a comparison as complete."""
    progress_complete[comparison_id] = True
