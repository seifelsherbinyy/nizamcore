"""classifier.py — Privacy class lookup for arbitrary repo paths.

Reads NIZAM__system/policies/PRIVACY_CLASSIFICATION.json and matches a
relative POSIX path to a classification:

  - strict_local_maximum  (generic hard-block from VPS/cloud)
  - strict_local          (encrypted volume only; ZDR inference permitted)
  - review_before_commit  (human review then commit)
  - private_github        (free to sync; private repo per locked Q3)
  - mirror_sanitized      (sanitized framework material)

Glob syntax: fnmatch + brace-expansion (`{a,b,c}` -> a|b|c).

Public API:
    classify(rel_path: str) -> str
    classify_many(paths: Iterable[str]) -> dict[str, str]
    is_egress_blocked(rel_path: str, target: str) -> tuple[bool, str]

Pure stdlib. No egress. Used by:
    - pre-commit hook
    - ledger_writer.py
    - sync_arbiter.py
    - Telegram gateway
"""
from __future__ import annotations

import fnmatch
import json
import re
from pathlib import Path
from typing import Iterable

_DEFAULT_REPO = Path(__file__).resolve().parents[2]
_CONFIG_PATH = _DEFAULT_REPO / "NIZAM__system" / "policies" / "PRIVACY_CLASSIFICATION.json"


# ─── Brace expansion ─────────────────────────────────────────────
_BRACE_RE = re.compile(r"\{([^{}]+)\}")


def _expand_braces(pattern: str) -> list[str]:
    """Expand `{a,b,c}` into a list of patterns. Handles nested? No: shallow
    only, which is sufficient for the privacy file format."""
    m = _BRACE_RE.search(pattern)
    if not m:
        return [pattern]
    pre = pattern[: m.start()]
    post = pattern[m.end():]
    alternatives = m.group(1).split(",")
    out: list[str] = []
    for alt in alternatives:
        for expanded in _expand_braces(pre + alt + post):
            out.append(expanded)
    return out


def _glob_to_regex(glob: str) -> str:
    """Convert glob to regex, expanding `**` to match any-depth."""
    # fnmatch.translate handles `*` and `?` but treats `**` as `*`.
    # We pre-replace `**` with a placeholder, then post-substitute.
    placeholder = "__DOUBLESTAR__"
    glob = glob.replace("**", placeholder)
    rx = fnmatch.translate(glob)
    rx = rx.replace(re.escape(placeholder), ".*")
    return rx


# ─── Loader ──────────────────────────────────────────────────────
_cache: dict[str, list[tuple[str, str]]] = {}


def _load_rules(config_path: Path = _CONFIG_PATH) -> list[tuple[str, str]]:
    """Load (path_glob, classification) pairs, brace-expanded."""
    key = str(config_path)
    if key in _cache:
        return _cache[key]
    data = json.loads(config_path.read_text(encoding="utf-8"))
    rules: list[tuple[str, str]] = []
    for rule in data.get("rules", []):
        glob = rule["path_glob"]
        cls = rule["classification"]
        for expanded in _expand_braces(glob):
            rules.append((expanded, cls))
    _cache[key] = rules
    return rules


def _default(config_path: Path = _CONFIG_PATH) -> str:
    data = json.loads(config_path.read_text(encoding="utf-8"))
    return data.get("default", "strict_local")


# ─── Public API ──────────────────────────────────────────────────
def classify(rel_path: str, config_path: Path = _CONFIG_PATH) -> str:
    """Classify `rel_path` (POSIX-style relative path) by most-specific rule.

    Strategy: scan rules in order; longer-matching globs win over shorter.
    Ties broken by later rule (later = more specific in our file order).
    """
    rules = _load_rules(config_path)
    # Normalize separators and strip a single leading "./" prefix.
    # NOTE: do NOT use lstrip("./") — it strips leading dots from dotfiles
    # (".gitignore" -> "gitignore"), silently mis-classifying them.
    rel = rel_path.replace("\\", "/")
    if rel.startswith("./"):
        rel = rel[2:]
    best: tuple[int, str] = (-1, _default(config_path))
    for glob, cls in rules:
        rx = _glob_to_regex(glob)
        if re.fullmatch(rx, rel):
            specificity = len(glob)
            if specificity >= best[0]:
                best = (specificity, cls)
    return best[1]


def classify_many(
    paths: Iterable[str], config_path: Path = _CONFIG_PATH
) -> dict[str, str]:
    return {p: classify(p, config_path) for p in paths}


# Egress matrix — what targets each classification may reach.
# Synchronized with sync_arbiter.Plane (single source of allowed targets).
EGRESS_MATRIX: dict[str, set[str]] = {
    "strict_local_maximum": set(),   # nothing leaves the local machine
    "strict_local":        {"laptop_disk", "vps_encrypted_volume",
                            "drive_crypt", "zdr_inference",
                            "telegram_operator"},
    "review_before_commit": {"laptop_disk", "vps_plaintext", "github_private",
                             "drive_clear", "zdr_inference",
                             "telegram_operator"},
    "private_github":      {"laptop_disk", "vps_plaintext", "github_private",
                            "drive_clear", "notion_sanitized",
                            "zdr_inference", "telegram_operator"},
    "mirror_sanitized":    {"laptop_disk", "vps_plaintext", "github_private",
                            "drive_clear", "notion_sanitized",
                            "zdr_inference", "telegram_operator"},
}


def is_egress_blocked(rel_path: str, target: str,
                      config_path: Path = _CONFIG_PATH) -> tuple[bool, str]:
    """Return (blocked, reason).

    Used by the pre-commit hook and any code attempting to externalize bytes.
    """
    cls = classify(rel_path, config_path)
    allowed = EGRESS_MATRIX.get(cls, set())
    if target in allowed:
        return False, f"ok: {cls} -> {target}"
    return True, (
        f"HIMAYAH refuses: classification '{cls}' "
        f"does not permit egress to '{target}' (allowed: {sorted(allowed)})"
    )


if __name__ == "__main__":
    # Tiny CLI: `python -m governor.classifier <path> [<target>]`
    import sys
    if len(sys.argv) < 2:
        print("usage: classifier.py <rel_path> [<target>]")
        sys.exit(2)
    path = sys.argv[1]
    cls = classify(path)
    print(f"{path} -> {cls}")
    if len(sys.argv) >= 3:
        blocked, reason = is_egress_blocked(path, sys.argv[2])
        print(f"egress -> {sys.argv[2]}: {'BLOCKED' if blocked else 'ALLOW'} ({reason})")
