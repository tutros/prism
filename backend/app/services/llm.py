"""Single entry point for Claude calls, with two backends.

LLM_BACKEND=api (default) calls the Anthropic API with ANTHROPIC_API_KEY.
LLM_BACKEND=cli runs Claude Code headless (`claude -p`), which uses the
logged-in Claude subscription. Personal, local use only; not for Docker.
"""

import asyncio
import json
import os
import shutil
import subprocess
from types import SimpleNamespace

from .config import get_anthropic_client
from .usage_tracker import record_usage

_BACKENDS = ("api", "cli")
_CLI_TIMEOUT_S = 300


class LLMError(RuntimeError):
    """A Claude call failed."""


def get_backend() -> str:
    """Return the configured backend; reject unknown values."""
    backend = os.environ.get("LLM_BACKEND", "api").strip().lower() or "api"
    if backend not in _BACKENDS:
        raise ValueError(
            f"LLM_BACKEND must be one of {', '.join(_BACKENDS)}, got {backend!r}"
        )
    return backend


def check_backend() -> None:
    """Validate the backend at startup; raise with a clear message if unusable."""
    if get_backend() == "cli" and shutil.which("claude") is None:
        raise RuntimeError(
            "LLM_BACKEND=cli needs the Claude Code CLI (`claude`) on PATH. "
            "Install and log in to Claude Code, or set LLM_BACKEND=api. "
            "CLI mode is not supported in Docker."
        )


async def complete(
    feature: str,
    model: str,
    system: str | list[dict],
    prompt: str,
    max_tokens: int,
) -> str:
    """Send one system prompt and one user message; return the reply text.

    `system` is a string or a list of API text blocks (which may carry
    cache_control). Usage is recorded under `feature`.
    """
    if get_backend() == "cli":
        return await _complete_cli(feature, model, system, prompt)
    return await _complete_api(feature, model, system, prompt, max_tokens)


async def _complete_api(feature, model, system, prompt, max_tokens) -> str:
    client = get_anthropic_client()
    response = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    record_usage(feature, model, response.usage)
    return response.content[0].text


def _system_text(system: str | list[dict]) -> str:
    if isinstance(system, str):
        return system
    return "\n\n".join(block["text"] for block in system)


def _cli_args(exe: str, model: str, system: str | list[dict]) -> list[str]:
    return [
        exe, "-p",
        "--output-format", "json",
        "--model", model,
        "--tools", "",
        "--system-prompt", _system_text(system),
        "--setting-sources", "",
    ]


def _parse_cli_output(stdout: str) -> dict | None:
    """Parse the JSON result; a warning line may precede it."""
    start = stdout.find("{")
    if start == -1:
        return None
    try:
        data, _ = json.JSONDecoder().raw_decode(stdout[start:])
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


async def _complete_cli(feature, model, system, prompt) -> str:
    # max_tokens has no CLI equivalent and is not passed.
    exe = shutil.which("claude")
    if exe is None:
        raise LLMError("LLM_BACKEND=cli but `claude` is not on PATH")
    # With ANTHROPIC_API_KEY set, `claude -p` bills the key, not the subscription.
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    try:
        proc = await asyncio.to_thread(
            subprocess.run,
            _cli_args(exe, model, system),
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            timeout=_CLI_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as e:
        raise LLMError(f"claude -p timed out after {_CLI_TIMEOUT_S}s") from e

    data = _parse_cli_output(proc.stdout or "")
    if data is not None and data.get("is_error"):
        status = data.get("api_error_status")
        raise LLMError(f"claude -p returned an error ({status}): {data.get('result')}")
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()[-500:]
        raise LLMError(f"claude -p exited with code {proc.returncode}: {detail}")
    if data is None or not isinstance(data.get("result"), str):
        raise LLMError("claude -p output had no JSON result")

    usage = data.get("usage") or {}
    record_usage(
        feature,
        model,
        SimpleNamespace(
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            cache_creation_input_tokens=usage.get("cache_creation_input_tokens", 0),
            cache_read_input_tokens=usage.get("cache_read_input_tokens", 0),
        ),
        backend="cli",
        cost_usd=float(data.get("total_cost_usd") or 0.0),
    )
    return data["result"]
