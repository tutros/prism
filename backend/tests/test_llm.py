"""Tests for the LLM backend switch (issue #24). Subprocess and SDK are mocked."""

import asyncio
import json
import subprocess
import threading
from types import SimpleNamespace

import pytest

from app.services import llm, spending_guard, usage_tracker

_SYSTEM_BLOCKS = [
    {"type": "text", "text": "Base."},
    {"type": "text", "text": "Cached.", "cache_control": {"type": "ephemeral"}},
]

_CLI_OK = {
    "type": "result",
    "is_error": False,
    "result": '```json\n{"ok": true}\n```',
    "total_cost_usd": 0.048,
    "usage": {
        "input_tokens": 10,
        "output_tokens": 5,
        "cache_creation_input_tokens": 23700,
        "cache_read_input_tokens": 0,
    },
}


@pytest.fixture
def recorded(monkeypatch, tmp_path):
    """Isolate usage records and the daily spend accumulator."""
    monkeypatch.setattr(usage_tracker, "_DATA_DIR", tmp_path)
    monkeypatch.setattr(usage_tracker, "_METRICS_FILE", tmp_path / "usage_metrics.json")
    monkeypatch.setattr(usage_tracker, "_usage_records", [])
    monkeypatch.setattr(spending_guard, "_daily_cost_usd", 0.0)
    return usage_tracker._usage_records


@pytest.fixture
def cli(monkeypatch):
    """Select the cli backend and fake `claude` on PATH and subprocess.run."""
    monkeypatch.setenv("LLM_BACKEND", "cli")
    monkeypatch.setattr(llm.shutil, "which", lambda name: "/bin/claude")
    calls = []

    def set_result(stdout="", returncode=0, stderr="", exc=None):
        def fake_run(args, **kwargs):
            calls.append(SimpleNamespace(args=args, kwargs=kwargs,
                                         thread=threading.current_thread()))
            if exc:
                raise exc
            return subprocess.CompletedProcess(args, returncode, stdout, stderr)
        monkeypatch.setattr(llm.subprocess, "run", fake_run)

    set_result(stdout=json.dumps(_CLI_OK))
    return SimpleNamespace(calls=calls, set_result=set_result)


def _complete(system=_SYSTEM_BLOCKS):
    return asyncio.run(llm.complete("criteria_quick", "claude-sonnet-4-5-20250929",
                                    system, "the prompt", 2048))


# -- Backend selection ----------------------------------------------------------

def test_backend_defaults_to_api(monkeypatch):
    monkeypatch.delenv("LLM_BACKEND", raising=False)
    assert llm.get_backend() == "api"


def test_unknown_backend_rejected(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "magic")
    with pytest.raises(ValueError, match="LLM_BACKEND"):
        llm.get_backend()
    with pytest.raises(ValueError):
        llm.check_backend()


def test_cli_without_claude_on_path_fails_check(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "cli")
    monkeypatch.setattr(llm.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="claude"):
        llm.check_backend()


def test_cli_with_claude_on_path_passes_check(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "cli")
    monkeypatch.setattr(llm.shutil, "which", lambda name: "/bin/claude")
    llm.check_backend()


def test_app_startup_runs_backend_check(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    monkeypatch.setenv("LLM_BACKEND", "cli")
    monkeypatch.setattr(llm.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="claude"):
        with TestClient(app):
            pass


# -- api backend ----------------------------------------------------------------

def test_api_backend_passes_system_blocks_and_records_usage(monkeypatch, recorded):
    monkeypatch.delenv("LLM_BACKEND", raising=False)
    seen = {}

    async def create(**kwargs):
        seen.update(kwargs)
        return SimpleNamespace(
            content=[SimpleNamespace(text="reply")],
            usage=SimpleNamespace(input_tokens=1000, output_tokens=100,
                                  cache_creation_input_tokens=0, cache_read_input_tokens=0),
        )

    monkeypatch.setattr(llm, "get_anthropic_client",
                        lambda: SimpleNamespace(messages=SimpleNamespace(create=create)))
    assert _complete() == "reply"
    assert seen["system"] == _SYSTEM_BLOCKS  # cache_control kept
    assert seen["max_tokens"] == 2048
    assert seen["messages"] == [{"role": "user", "content": "the prompt"}]
    assert recorded[-1]["backend"] == "api"
    assert spending_guard._daily_cost_usd == pytest.approx(recorded[-1]["cost_usd"])
    assert spending_guard._daily_cost_usd > 0


# -- cli backend ----------------------------------------------------------------

def test_cli_runs_claude_with_expected_flags(cli, recorded):
    assert _complete() == _CLI_OK["result"]
    call = cli.calls[-1]
    assert call.args == [
        "/bin/claude", "-p",
        "--output-format", "json",
        "--model", "claude-sonnet-4-5-20250929",
        "--tools", "",
        "--system-prompt", "Base.\n\nCached.",
        "--setting-sources", "",
    ]
    assert call.kwargs["input"] == "the prompt"
    assert call.kwargs["timeout"] > 0


def test_cli_accepts_string_system(cli, recorded):
    _complete(system="Plain system.")
    args = cli.calls[-1].args
    assert args[args.index("--system-prompt") + 1] == "Plain system."


def test_cli_strips_api_key_from_child_env(cli, recorded, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-should-not-leak")
    monkeypatch.setenv("SOME_OTHER_VAR", "kept")
    _complete()
    env = cli.calls[-1].kwargs["env"]
    assert "ANTHROPIC_API_KEY" not in env
    assert env["SOME_OTHER_VAR"] == "kept"


def test_cli_runs_off_the_event_loop_thread(cli, recorded):
    _complete()
    assert cli.calls[-1].thread is not threading.main_thread()


def test_cli_does_not_need_api_key(cli, recorded, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def boom():
        raise AssertionError("API client must not be built in cli mode")

    monkeypatch.setattr(llm, "get_anthropic_client", boom)
    assert _complete() == _CLI_OK["result"]


def test_cli_parses_after_leading_warning(cli, recorded):
    cli.set_result(stdout="Warning: something odd\n" + json.dumps(_CLI_OK))
    assert _complete() == _CLI_OK["result"]


@pytest.mark.parametrize("kwargs", [
    {"stdout": "", "returncode": 1, "stderr": "boom"},
    {"stdout": json.dumps({**_CLI_OK, "is_error": True, "result": "Credit balance is too low",
                           "api_error_status": 400}), "returncode": 1},
    {"stdout": json.dumps({**_CLI_OK, "is_error": True, "result": "bad"})},
    {"stdout": "not json at all"},
    {"stdout": "{ truncated"},
    {"exc": subprocess.TimeoutExpired(cmd="claude", timeout=1)},
], ids=["nonzero-exit", "is-error-nonzero", "is-error-zero", "no-json", "bad-json", "timeout"])
def test_cli_errors_raise(cli, recorded, kwargs):
    cli.set_result(**kwargs)
    with pytest.raises(llm.LLMError):
        _complete()
    assert recorded == []


def test_cli_usage_recorded_but_not_counted_toward_cap(cli, recorded):
    _complete()
    rec = recorded[-1]
    assert rec["backend"] == "cli"
    assert rec["feature"] == "criteria_quick"
    assert rec["cost_usd"] == pytest.approx(0.048)
    assert rec["cache_creation_tokens"] == 23700
    assert spending_guard._daily_cost_usd == 0.0


def test_monitoring_stats_keep_cli_out_of_real_spend(cli, recorded):
    _complete()
    stats = usage_tracker.get_usage_stats()
    assert stats["total_cost_usd"] == 0.0
    assert stats["cli_notional_cost_usd"] == pytest.approx(0.048)
    assert stats["by_feature"]["criteria_quick"]["count"] == 1


# -- Spending cap rebuild on startup ---------------------------------------------

def test_startup_rebuild_skips_cli_records(monkeypatch, tmp_path):
    from datetime import date
    today = date.today().isoformat() + "T12:00:00+00:00"
    metrics = tmp_path / "usage_metrics.json"
    metrics.write_text(json.dumps([
        {"cost_usd": 1.0, "timestamp": today},                    # legacy, no backend
        {"cost_usd": 0.5, "timestamp": today, "backend": "api"},
        {"cost_usd": 9.0, "timestamp": today, "backend": "cli"},
    ]))
    monkeypatch.setattr(spending_guard, "_daily_cost_usd", 0.0)
    spending_guard._load_today_cost(metrics)
    assert spending_guard._daily_cost_usd == pytest.approx(1.5)
