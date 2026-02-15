from pathlib import Path
import json
import os
import re
import tempfile

from pydantic import ValidationError

from .models import ComparisonResult

# UUID4 pattern for validating comparison IDs
_UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)


def _validate_comparison_id(comparison_id: str) -> None:
    """Validate comparison_id is a UUID to prevent path traversal."""
    if not _UUID_RE.match(comparison_id):
        raise ValueError(f"Invalid comparison_id: {comparison_id}")


class JSONStorage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def write_result(self, comparison_id: str, data: ComparisonResult) -> None:
        """Atomically write JSON to prevent corruption on crash."""
        _validate_comparison_id(comparison_id)
        target_path = self.data_dir / f"{comparison_id}.json"

        # Write to temp file in same directory (required for atomic os.replace)
        fd, tmp_path = tempfile.mkstemp(dir=self.data_dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as tmp:
                json.dump(data.model_dump(mode="json"), tmp, indent=2, default=str)
                tmp.flush()
                os.fsync(tmp.fileno())
            # Atomic rename — overwrites target if it exists
            os.replace(tmp_path, target_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def read_result(self, comparison_id: str) -> ComparisonResult | None:
        """Read a comparison result by ID, or None if not found."""
        _validate_comparison_id(comparison_id)
        target_path = self.data_dir / f"{comparison_id}.json"
        if not target_path.exists():
            return None
        try:
            data = json.loads(target_path.read_text())
            return ComparisonResult.model_validate(data)
        except (ValidationError, json.JSONDecodeError):
            return None

    def list_results(self) -> list[str]:
        """Return list of comparison IDs stored on disk."""
        return [p.stem for p in self.data_dir.glob("*.json") if _UUID_RE.match(p.stem)]
