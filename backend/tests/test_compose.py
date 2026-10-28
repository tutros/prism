"""
Guards on the Docker Compose files (from the codex review of PR #5, M-1).

The structural tests need only PyYAML and run everywhere. The rendering test
shells out to `docker compose config` and is skipped when Docker is absent.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
PROD = ROOT / "docker-compose.yml"
DEV = ROOT / "docker-compose.override.yml"


class _Loader(yaml.SafeLoader):
    """SafeLoader that tolerates Compose's !reset / !override merge tags."""


def _tagged(loader, node):
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    if isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    return None


for _tag in ("!reset", "!override"):
    _Loader.add_constructor(_tag, _tagged)


def load(path: Path) -> dict:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=_Loader)


def assert_data_volume_is_project_scoped(cfg: dict) -> None:
    """Shared with the negative check against the pre-fix file in the PR."""
    vol = cfg["volumes"]["prism-data"]
    assert not vol or "name" not in vol, (
        "an explicit name: makes every Compose project on the host share one data volume"
    )
    assert "prism-data:/app/data" in cfg["services"]["backend"]["volumes"]


# -- production file ----------------------------------------------------------

def test_production_data_volume_is_project_scoped():
    assert_data_volume_is_project_scoped(load(PROD))


def test_production_backend_is_not_published_and_frontend_is_port_80():
    cfg = load(PROD)
    assert "ports" not in cfg["services"]["backend"]
    assert cfg["services"]["frontend"]["ports"] == ["80:80"]


# -- dev override -------------------------------------------------------------

def test_dev_override_replaces_rather_than_merges():
    raw = DEV.read_text(encoding="utf-8")
    # These three tags are what stop the base file's build block, 80:80 port and
    # named volume from leaking into the dev stack.
    assert "build: !reset null" in raw
    assert "ports: !override" in raw
    assert "volumes: !override" in raw
    dev = load(DEV)
    assert dev["services"]["frontend"]["ports"] == ["5173:5173"]
    backend_volumes = dev["services"]["backend"]["volumes"]
    assert "./backend:/app" in backend_volumes
    assert not any("prism-data" in v for v in backend_volumes)


# -- rendered by Docker (skipped without a daemon) -----------------------------

@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not installed")
def test_rendered_volume_sources_differ_per_project(tmp_path):
    # Copy the production file next to an empty .env so `config` does not fail
    # on the env_file reference; contexts are not read by `config`.
    (tmp_path / "docker-compose.yml").write_text(PROD.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / ".env").write_text("", encoding="utf-8")
    sources = {}
    for project in ("alpha", "beta"):
        out = subprocess.run(
            ["docker", "compose", "-p", project, "-f", "docker-compose.yml", "config", "--format", "json"],
            cwd=tmp_path, capture_output=True, text=True, check=True,
        ).stdout
        mounts = [m for m in json.loads(out)["services"]["backend"]["volumes"] if m["target"] == "/app/data"]
        assert len(mounts) == 1 and mounts[0]["type"] == "volume"
        sources[project] = mounts[0]["source"]
    assert sources["alpha"] != sources["beta"], sources
