#!/usr/bin/env python3
"""nizam_router.py — deterministic intent → codename resolver (IR-1..IR-8).

Shared by router_dry_run, relay coordinator, and nizam-governor. Stdlib only.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def _strip_comment(s: str) -> str:
    out: list[str] = []
    in_str = False
    quote = ""
    prev = " "
    for ch in s:
        if not in_str and ch == "#" and (prev == " " or prev == "\t" or prev == ""):
            break
        if ch in "\"'":
            if not in_str:
                in_str = True
                quote = ch
            elif quote == ch:
                in_str = False
        out.append(ch)
        prev = ch
    return "".join(out)


def _parse_scalar(s: str):
    s = s.strip()
    if not s:
        return ""
    if s in ("null", "~"):
        return None
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False
    if (s[0], s[-1]) in (("\"", "\""), ("'", "'")):
        return s[1:-1]
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"-?\d+\.\d+", s):
        return float(s)
    return s


def _parse_inline_object(s: str) -> dict:
    inner = s.strip()[1:-1].strip()
    out: dict = {}
    parts: list[str] = []
    depth = 0
    cur = ""
    for ch in inner:
        if ch in "{[(":
            depth += 1
        elif ch in "}])":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    for p in parts:
        k, _, v = p.partition(":")
        out[k.strip()] = _parse_scalar(v)
    return out


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _parse_list(lines: list[str], base: int) -> list:
    out: list = []
    for line in lines:
        if _indent(line) != base:
            continue
        s = line.strip()
        if not s.startswith("- "):
            continue
        rest = s[2:].strip()
        if rest.startswith("{") and rest.endswith("}"):
            out.append(_parse_inline_object(rest))
        else:
            out.append(_parse_scalar(rest))
    return out


def _parse_block(lines: list[str], base: int) -> dict:
    out: dict = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        ind = _indent(line)
        if ind < base:
            break
        if ind > base:
            i += 1
            continue
        stripped = line.strip()
        if stripped.startswith("- "):
            break
        key, sep, rest = stripped.partition(":")
        if not sep:
            i += 1
            continue
        key = key.strip()
        rest = rest.strip()
        if rest.startswith("{") and rest.endswith("}"):
            out[key] = _parse_inline_object(rest)
            i += 1
            continue
        if rest:
            out[key] = _parse_scalar(rest)
            i += 1
            continue
        child_lines = []
        j = i + 1
        while j < len(lines) and _indent(lines[j]) > base:
            child_lines.append(lines[j])
            j += 1
        if child_lines and child_lines[0].strip().startswith("- "):
            out[key] = _parse_list(child_lines, _indent(child_lines[0]))
        else:
            out[key] = _parse_block(child_lines, _indent(child_lines[0]) if child_lines else base + 2)
        i = j
    return out


def _read_yaml(path: Path) -> dict:
    lines = [
        _strip_comment(line).rstrip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if _strip_comment(line).strip()
    ]
    return _parse_block(lines, 0)

CRISIS_KEYWORDS = {
    "crisis", "emergency", "panic", "overload red",
    "i can't breathe", "can't breathe", "suicidal",
}
AHEL_MARKERS = re.compile(r"(?i)(#ahel\b|\[ahel\]|#family\b|\[family\])")
KIN_TERMS = re.compile(
    r"(?i)\b(sister|brother|mother|father|mom|dad|wife|husband|son|daughter)\b"
)
OCCASION_TERMS = re.compile(
    r"(?i)\b(graduation|wedding|anniversary|birthday|ceremony|reunion)\b"
)
PLANNING_TERMS = re.compile(
    r"(?i)\b(plan|planning|prepare|organizing|organise|something special|next month)\b"
)
HABIT_OPENER = re.compile(r"(?i)\bwhat do you think about\b")
HABIT_LEXICON = re.compile(
    r"(?i)\b(coffee|caffeine|sleep|alcohol|screen time|screens|sugar|nicotine)\b"
)
BIOMETRIC_CMD = re.compile(r"^/pulse\b", re.I)
BIOMETRIC_TRIPLET = re.compile(
    r"(?i)recovery\D*([0-9]+(?:\.[0-9]+)?).*(?:hrv)\D*([0-9]+(?:\.[0-9]+)?).*(?:strain)\D*([0-9]+(?:\.[0-9]+)?)"
)
DUMP_MARKERS = re.compile(
    r"(?i)\b(dump before i forget|/tafrigh-capture|/dump\b|random thought)\b"
)

META_KEYS = frozenset({
    "schema_version", "marked_as_starter", "last_tuned_from_traffic", "tuning_owner",
})


def load_config(path: Path) -> dict:
    return _read_yaml(path)


def load_exemplars(path: Path) -> dict:
    return _read_yaml(path)


def _detect_kind(text: str) -> str:
    low = text.lower()
    if any(k in low for k in CRISIS_KEYWORDS):
        return "CRISIS"
    if low.startswith("/"):
        return "COMMAND"
    return "TRIGGER"


def _command_lookup(text: str, commands: dict) -> tuple[str | None, str | None, float, str]:
    """IR-1: registry before exemplars. Returns (target, bucket, conf, step)."""
    low = text.lower().strip()
    cmd_token = low.split()[0] if low.startswith("/") else ""
    for cmd, spec in (commands or {}).items():
        if not isinstance(spec, dict):
            continue
        if cmd_token == cmd.lower() or low.startswith(cmd.lower() + " "):
            if spec.get("control"):
                return None, None, 0.0, "IR-1:command_control"
            target = spec.get("target")
            if target:
                return target, "command_registry", 1.0, "IR-1:command_registry"
    return None, None, 0.0, ""


def _detector_biometric(text: str) -> tuple[str | None, str | None, float, str]:
    """IR-2."""
    if BIOMETRIC_CMD.search(text.strip()):
        return "Hayat", "biometric_log", 0.95, "IR-2:biometric_command"
    if BIOMETRIC_TRIPLET.search(text):
        return "Hayat", "biometric_log", 0.92, "IR-2:biometric_triplet"
    low = text.lower()
    if re.search(r"(?i)\bhrv\b", text) and re.search(r"(?i)\brecovery\b", text):
        return "Hayat", "biometric_log", 0.88, "IR-2:biometric_partial"
    if re.search(r"(?i)\bhrv\b", text):
        return "Hayat", "biometric_log", 0.87, "IR-2:hrv_mention"
    return None, None, 0.0, ""


def _detector_occasion_tactical(text: str) -> tuple[str | None, str | None, float, str]:
    """IR-3 + IR-7 (kin + planning → Khalid unless AHEL)."""
    if AHEL_MARKERS.search(text):
        return None, None, 0.0, ""
    if OCCASION_TERMS.search(text) and PLANNING_TERMS.search(text):
        return "Khalid", "tactical_plan", 0.90, "IR-3:occasion_tactical"
    if KIN_TERMS.search(text) and PLANNING_TERMS.search(text):
        return "Khalid", "tactical_plan", 0.86, "IR-7:kin_planning"
    return None, None, 0.0, ""


def _detector_habit_brainstorm(text: str) -> tuple[str | None, str | None, float, str]:
    """IR-4."""
    if HABIT_OPENER.search(text) and HABIT_LEXICON.search(text):
        return "Salman", "brainstorm", 0.88, "IR-4:habit_cothink"
    return None, None, 0.0, ""


def _detector_dump_capture(text: str) -> tuple[str | None, str | None, float, str]:
    """IR-5."""
    if DUMP_MARKERS.search(text):
        return "Amin", "capture", 0.85, "IR-5:explicit_dump"
    return None, None, 0.0, ""


def _match_exemplars(text: str, exemplars: dict) -> tuple[str, float]:
    low = text.lower()
    best_bucket = "capture"
    best_score = 0.0
    for bucket, items in exemplars.items():
        if bucket in META_KEYS or not isinstance(items, list):
            continue
        score = 0.0
        for ex in items:
            ex_s = str(ex)
            if ex_s.startswith("_negative:"):
                continue
            ex_low = ex_s.lower()
            if ex_low.startswith("/") and low.startswith(ex_low.split()[0]):
                score = max(score, 1.0)
            tokens_a = set(re.findall(r"[a-z0-9-]+", ex_low))
            tokens_b = set(re.findall(r"[a-z0-9-]+", low))
            if tokens_a and tokens_b:
                jacc = len(tokens_a & tokens_b) / max(len(tokens_a | tokens_b), 1)
                score = max(score, jacc)
        if HABIT_OPENER.search(text) and bucket == "capture":
            score *= 0.25
        if PLANNING_TERMS.search(text) and OCCASION_TERMS.search(text) and bucket == "brainstorm":
            score *= 0.35
        if score > best_score:
            best_score = score
            best_bucket = bucket
    return best_bucket, best_score


def _route_action(conf: float, route_conf: dict) -> str:
    auto_min = float(route_conf.get("auto_route_min", 0.70))
    confirm_min = float(route_conf.get("confirm_band_min", 0.50))
    if conf >= auto_min:
        return "auto_route"
    if conf >= confirm_min:
        return "confirm_band"
    return "fallback_capture"


def resolve(
    text: str,
    config: dict,
    exemplars: dict,
    *,
    sukoon_hot: bool = False,
) -> dict[str, Any]:
    """Full resolve path. IR-6: sukoon_overlay never changes target."""
    steps: list[str] = []
    intents_map = config.get("intents", {})
    route_conf = config.get("route_confidence", {})
    commands = config.get("commands", {})

    kind = _detect_kind(text)
    steps.append(f"kind:{kind}")

    if kind == "CRISIS":
        return {
            "kind": "CRISIS",
            "target": "protocol:crisis_sukoon_red",
            "bucket": "crisis",
            "confidence": 1.0,
            "route_action": "auto_route",
            "resolver_steps": steps,
            "sukoon_overlay": False,
            "target_swap_blocked_by_ir6": False,
        }

    # IR-1 commands
    tgt, bucket, conf, step = _command_lookup(text, commands)
    if step:
        steps.append(step)
        return _finish(kind, tgt, bucket, conf, "auto_route", steps, sukoon_hot)

    # IR-2 .. IR-5 detectors (ordered)
    for detector in (
        _detector_biometric,
        _detector_occasion_tactical,
        _detector_habit_brainstorm,
        _detector_dump_capture,
    ):
        tgt, bucket, conf, step = detector(text)
        if step:
            steps.append(step)
            action = "auto_route" if conf >= float(route_conf.get("auto_route_min", 0.70)) else "auto_route"
            return _finish(kind, tgt, bucket, conf, action, steps, sukoon_hot)

    # Exemplar fallback
    bucket, conf = _match_exemplars(text, exemplars)
    steps.append(f"exemplar:{bucket}")
    intent = intents_map.get(bucket, {})
    tgt = intent.get("target", "Amin") if isinstance(intent, dict) else "Amin"
    action = _route_action(conf, route_conf)
    if action == "fallback_capture":
        tgt = intents_map.get("capture", {}).get("target", "Amin")
        bucket = "capture"
        steps.append("IR-8:fallback_capture")
    return _finish(kind, tgt, bucket, conf, action, steps, sukoon_hot)


def _finish(
    kind: str,
    target: str | None,
    bucket: str | None,
    conf: float,
    action: str,
    steps: list[str],
    sukoon_hot: bool,
) -> dict[str, Any]:
    target = target or "Amin"
    overlay = bool(
        sukoon_hot
        and target not in ("protocol:crisis_sukoon_red",)
        and not target.startswith("governor:")
    )
    if overlay:
        steps.append("IR-6:sukoon_overlay_tone_only")
    return {
        "kind": kind,
        "target": target,
        "bucket": bucket or "",
        "confidence": round(conf, 3),
        "route_action": action,
        "resolver_steps": steps,
        "sukoon_overlay": overlay,
        "target_swap_blocked_by_ir6": overlay,
    }
