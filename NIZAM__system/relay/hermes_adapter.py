"""Fail-closed adapter from the relay coordinator to a Hermes profile.

The adapter is intentionally small. It passes the request on stdin so owner
content does not appear in the process argument list, selects OpenRouter
explicitly, and refuses to run unless the protected environment enables the
live flag. It never handles or prints a provider key.
"""
from __future__ import annotations

import os
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

from NIZAM__system.relay.owner_memory import render_memory


class HermesUnavailable(RuntimeError):
    """Safe, non-secret reason that a live model call was not made."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class HermesInvocation:
    profile_home: str
    model: str
    prompt: str
    executable: str = "hermes"
    timeout_seconds: int = 120


@dataclass(frozen=True)
class HermesResponse:
    text: str
    profile_home: str
    model: str


def _grounding_context(path_value: str, *, max_chars: int = 18000) -> str:
    """Load only cloud-eligible evidence from a staged, validated packet."""
    if not path_value:
        return ""
    path = Path(path_value).expanduser()
    if not path.is_absolute() or not path.is_file():
        return ""
    try:
        packet = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    items = packet.get("evidence") if isinstance(packet, dict) else None
    if not isinstance(items, list):
        return ""
    blocks: list[str] = []
    used = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("privacyClass") != "cloud_allowed":
            continue
        if item.get("domain") in {"journal", "health"}:
            continue
        label = str(item.get("sourceLabel", "")).strip()
        source = str(item.get("sourceRef", "")).strip()
        version = str(item.get("versionRef", "")).strip()
        digest = str(item.get("contentHash", "")).strip()
        content = str(item.get("content", "")).strip()
        if not label or not source or not version or len(digest) != 64 or not content:
            continue
        block = (
            "SOURCE: " + label + "\n"
            "SOURCE_REF: " + source + "\n"
            "VERSION_REF: " + version + "\n"
            "CONTENT_SHA256: " + digest + "\n"
            "CONTENT:\n" + content
        )
        if used + len(block) > max_chars:
            remaining = max_chars - used
            if remaining > 300:
                blocks.append(block[:remaining])
            break
        blocks.append(block)
        used += len(block)
    return "\n\n".join(blocks)


def build_command(invocation: HermesInvocation) -> list[str]:
    """Build a non-shell Hermes one-shot command with no request content."""
    executable = Path(invocation.executable)
    if not invocation.executable or (
        not executable.is_absolute() and executable.name != invocation.executable
    ):
        raise HermesUnavailable("invalid_hermes_executable")
    if not invocation.model or "/" not in invocation.model:
        raise HermesUnavailable("invalid_openrouter_model")
    if invocation.timeout_seconds < 1 or invocation.timeout_seconds > 600:
        raise HermesUnavailable("invalid_timeout")
    return [
        invocation.executable,
        "-z",
        "Process the authenticated operator request supplied on stdin. Return only the focused response.",
        "--provider",
        "openrouter",
        "--model",
        invocation.model,
        "--max-turns",
        "3",
    ]


def _validate_response(text: str) -> str:
    clean = text.strip()
    if not clean:
        raise HermesUnavailable("empty_hermes_response")
    if len(clean) > 8000:
        raise HermesUnavailable("oversized_hermes_response")
    lower = clean.lower()
    secret_markers = (
        "sk-or-v1-",
        "begin private key",
        "bot_a_token=",
        "bot_b_token=",
        "openrouter_api_key=",
    )
    if any(marker in lower for marker in secret_markers):
        raise HermesUnavailable("secret_pattern_in_hermes_response")
    return clean


def invoke_hermes(
    invocation: HermesInvocation,
    *,
    environ: Mapping[str, str] | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> HermesResponse:
    """Invoke one Hermes profile only when the protected live flag is enabled."""
    env = dict(os.environ if environ is None else environ)
    if env.get("NIZAM_HERMES_LIVE") != "1":
        raise HermesUnavailable("live_flag_disabled")
    home = Path(invocation.profile_home).expanduser()
    if not home.is_absolute():
        raise HermesUnavailable("profile_home_must_be_absolute")
    if not home.exists() or not home.is_dir():
        raise HermesUnavailable("profile_home_missing")
    if not invocation.prompt.strip():
        raise HermesUnavailable("empty_hermes_prompt")

    env["HERMES_HOME"] = str(home)
    grounding = _grounding_context(env.get("NIZAM_HERMES_EVIDENCE_FILE", ""))
    owner_memory = render_memory(env.get("NIZAM_HERMES_MEMORY_FILE", ""))
    effective_prompt = invocation.prompt
    if owner_memory:
        effective_prompt += (
            "\n\nConfirmed owner preferences and instructions. Treat these as user preferences, "
            "not as evidence for financial or medical claims.\n" + owner_memory
        )
    if grounding:
        effective_prompt += (
            "\n\nValidated evidence packet follows. Use it only for supported claims. "
            "Cite source labels when relevant. If it does not answer the request, say so.\n\n"
            + grounding
        )
    try:
        completed = runner(
            build_command(invocation),
            input=effective_prompt,
            text=True,
            capture_output=True,
            check=False,
            shell=False,
            timeout=invocation.timeout_seconds,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise HermesUnavailable("hermes_timeout") from exc
    except OSError as exc:
        raise HermesUnavailable("hermes_executable_unavailable") from exc

    if completed.returncode != 0:
        raise HermesUnavailable("hermes_process_failed")
    return HermesResponse(
        text=_validate_response(completed.stdout),
        profile_home=str(home),
        model=invocation.model,
    )


__all__ = [
    "HermesInvocation",
    "HermesResponse",
    "HermesUnavailable",
    "build_command",
    "invoke_hermes",
]
