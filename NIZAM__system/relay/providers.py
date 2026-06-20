"""Stdlib-only LLM providers for approved live persona runtime."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from NIZAM__system.relay.persona_runtime import PersonaRuntimeRequest


class OpenAIProvider:
    name = "openai"
    model = os.environ.get("NIZAM_OPENAI_MODEL", "gpt-4o-mini")
    local_only = False

    def invoke(self, request: PersonaRuntimeRequest) -> dict:
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY missing")
        system = request.system_prompt or (
            "You are Amin, NIZAM's capture persona. Reply warmly and concisely. "
            "Confirm what was captured without inventing facts."
        )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": request.input_text},
            ],
            "max_tokens": 300,
        }
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=request.timeout_seconds) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        choice = body["choices"][0]["message"]["content"]
        usage = body.get("usage", {})
        return {
            "reply": str(choice).strip(),
            "input_tokens": int(usage.get("prompt_tokens", 0)),
            "output_tokens": int(usage.get("completion_tokens", 0)),
            "cost_usd": 0.0,
        }


class AnthropicProvider:
    name = "anthropic"
    model = os.environ.get("NIZAM_ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    local_only = False

    def invoke(self, request: PersonaRuntimeRequest) -> dict:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY missing")
        system = request.system_prompt or (
            "You are Amin, NIZAM's capture persona. Reply warmly and concisely. "
            "Confirm what was captured without inventing facts."
        )
        payload = {
            "model": self.model,
            "max_tokens": 300,
            "system": system,
            "messages": [{"role": "user", "content": request.input_text}],
        }
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=request.timeout_seconds) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        parts = body.get("content", [])
        text = "".join(part.get("text", "") for part in parts if part.get("type") == "text")
        usage = body.get("usage", {})
        return {
            "reply": text.strip(),
            "input_tokens": int(usage.get("input_tokens", 0)),
            "output_tokens": int(usage.get("output_tokens", 0)),
            "cost_usd": 0.0,
        }


class OpenRouterProvider:
    name = "openrouter"
    model = os.environ.get(
        "NIZAM_OPENROUTER_MODEL", "deepseek/deepseek-v4-flash"
    )
    local_only = False

    def invoke(self, request: PersonaRuntimeRequest) -> dict:
        api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY missing")
        system = request.system_prompt or (
            "You are Amin, NIZAM's capture persona. Reply warmly and concisely. "
            "Confirm what was captured without inventing facts."
        )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": request.input_text},
            ],
            "max_tokens": 300,
            "provider": {"data_collection": "deny"},
        }
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/seifelsherbinyy/nizamcore",
                "X-Title": "NIZAM Relay",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=request.timeout_seconds) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        choice = body["choices"][0]["message"]["content"]
        usage = body.get("usage", {})
        return {
            "reply": str(choice).strip(),
            "input_tokens": int(usage.get("prompt_tokens", 0)),
            "output_tokens": int(usage.get("completion_tokens", 0)),
            "cost_usd": 0.0,
        }


def build_provider():
    if os.environ.get("OPENROUTER_API_KEY", "").strip():
        return OpenRouterProvider()
    if os.environ.get("OPENAI_API_KEY", "").strip():
        return OpenAIProvider()
    if os.environ.get("ANTHROPIC_API_KEY", "").strip():
        return AnthropicProvider()
    return None
