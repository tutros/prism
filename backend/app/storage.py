from pathlib import Path
import json
import os
import tempfile

from pydantic import ValidationError

from .models import ComparisonResult


class JSONStorage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def write_result(self, comparison_id: str, data: ComparisonResult) -> None:
        """Atomically write JSON to prevent corruption on crash."""
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
        return [p.stem for p in self.data_dir.glob("*.json")]
