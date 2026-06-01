from pathlib import Path
import json
import os
import re
import tempfile

from pydantic import ValidationError

from .models import Decision, AnalysisResult

_UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)


def _validate_id(value: str, label: str = "id") -> None:
    if not _UUID_RE.match(value):
        raise ValueError(f"Invalid {label}: {value}")


class JSONStorage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        (self.data_dir / "decisions").mkdir(parents=True, exist_ok=True)

    def _decision_path(self, decision_id: str) -> Path:
        return self.data_dir / "decisions" / f"{decision_id}.json"

    def _analysis_path(self, decision_id: str, analysis_id: str) -> Path:
        return self.data_dir / "decisions" / decision_id / "analyses" / f"{analysis_id}.json"

    def _atomic_write(self, target_path: Path, data: dict) -> None:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=target_path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as tmp:
                json.dump(data, tmp, indent=2, default=str)
                tmp.flush()
                os.fsync(tmp.fileno())
            os.replace(tmp_path, target_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def write_decision(self, decision: Decision) -> None:
        _validate_id(decision.id, "decision_id")
        self._atomic_write(
            self._decision_path(decision.id),
            decision.model_dump(mode="json"),
        )

    def read_decision(self, decision_id: str) -> Decision | None:
        _validate_id(decision_id, "decision_id")
        path = self._decision_path(decision_id)
        if not path.exists():
            return None
        try:
            return Decision.model_validate(json.loads(path.read_text()))
        except (ValidationError, json.JSONDecodeError):
            return None

    def list_decisions(self) -> list[str]:
        decisions_dir = self.data_dir / "decisions"
        return [p.stem for p in decisions_dir.glob("*.json") if _UUID_RE.match(p.stem)]

    def write_analysis(self, analysis: AnalysisResult) -> None:
        _validate_id(analysis.decision_id, "decision_id")
        _validate_id(analysis.analysis_id, "analysis_id")
        self._atomic_write(
            self._analysis_path(analysis.decision_id, analysis.analysis_id),
            analysis.model_dump(mode="json"),
        )

    def read_analysis(self, decision_id: str, analysis_id: str) -> AnalysisResult | None:
        _validate_id(decision_id, "decision_id")
        _validate_id(analysis_id, "analysis_id")
        path = self._analysis_path(decision_id, analysis_id)
        if not path.exists():
            return None
        try:
            return AnalysisResult.model_validate(json.loads(path.read_text()))
        except (ValidationError, json.JSONDecodeError):
            return None

    def list_analyses(self, decision_id: str) -> list[str]:
        _validate_id(decision_id, "decision_id")
        analyses_dir = self.data_dir / "decisions" / decision_id / "analyses"
        if not analyses_dir.exists():
            return []
        return [p.stem for p in analyses_dir.glob("*.json") if _UUID_RE.match(p.stem)]
