from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from ..contracts import ContextRefresh
from .contracts import EvidenceRef

_JOURNAL_BODY_KEYS = frozenset(
    {
        "body",
        "journal_body",
        "entry_text",
        "raw_text",
        "content",
        "full_text",
        "transcript",
        "message",
        "reflection",
    }
)

_SOURCE_KIND = {
    "yawmiyat_journal": "journal_meta",
    "witness_reflection": "journal_meta",
    "whoop_badan": "body_signal",
    "pulse_entries": "body_signal",
    "sukoon_capacity": "capacity",
    "open_loops": "open_loop",
    "active_decisions": "decision_meta",
    "thabat_summary": "ledger_excerpt",
    "recent_interactions": "interaction_meta",
}


def _hash_excerpt(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _scrub_journal_bodies(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            if key in _JOURNAL_BODY_KEYS:
                continue
            cleaned[key] = _scrub_journal_bodies(item)
        return cleaned
    if isinstance(value, list):
        return [_scrub_journal_bodies(item) for item in value]
    if isinstance(value, str) and len(value) > 240:
        return value[:240] + "…"
    return value


def _summary_for_source(source_key: str, facts: dict[str, Any]) -> str:
    if source_key == "yawmiyat_journal":
        entry_date = facts.get("entry_date")
        title_present = facts.get("title_present")
        parts = []
        if entry_date:
            parts.append(f"entry {entry_date}")
        if title_present:
            parts.append("title present")
        return "; ".join(parts) or "journal metadata only"
    if source_key == "witness_reflection":
        parts = [
            str(facts[key])
            for key in ("session_type", "capacity_level")
            if facts.get(key)
        ]
        return "; ".join(parts) or "witness metadata only"
    if source_key == "whoop_badan":
        metrics = facts.get("metrics") or {}
        if metrics:
            return "metrics: " + ", ".join(f"{k}={v}" for k, v in metrics.items())
        return "body metrics present"
    if source_key == "pulse_entries":
        recovery = facts.get("recovery")
        band = facts.get("capacity_band")
        if recovery is not None:
            return f"recovery {recovery}" + (f" ({band})" if band else "")
        return "pulse entry present"
    if source_key == "open_loops":
        return f"{facts.get('open_loop_count', 0)} open loop(s)"
    if source_key == "active_decisions":
        return f"{facts.get('decision_count', 0)} recent decision(s)"
    if source_key == "thabat_summary":
        actions = facts.get("recent_actions") or []
        return "actions: " + ", ".join(actions[-3:]) if actions else "ledger continuity"
    if source_key == "sukoon_capacity":
        return f"capacity {facts.get('capacity', 'unknown')}"
    if source_key == "recent_interactions":
        return f"{facts.get('interaction_count', 0)} interaction(s)"
    return json.dumps(facts, sort_keys=True)[:240]


def build_evidence_pack(refresh: ContextRefresh) -> list[EvidenceRef]:
    """Build council evidence from pulsation ContextRefresh without journal egress."""
    refs: list[EvidenceRef] = []

    for source_key in refresh.sources_found:
        raw_facts = refresh.source_snapshots.get(source_key, {})
        facts = _scrub_journal_bodies(raw_facts)
        if not isinstance(facts, dict):
            facts = {}
        refs.append(
            EvidenceRef(
                ref_id=f"source:{source_key}",
                kind=_SOURCE_KIND.get(source_key, "summary"),
                source=source_key,
                summary=_summary_for_source(source_key, facts)[:240],
                hash_excerpt=_hash_excerpt(facts),
            )
        )

    for source_key in ("yawmiyat_journal", "witness_reflection"):
        if source_key not in refresh.sources_found:
            continue
        latest = refresh.latest_entry_timestamps.get(source_key)
        if not latest:
            continue
        refs.append(
            EvidenceRef(
                ref_id=f"journal_ref:{source_key}",
                kind="journal_ref",
                source=f"{source_key}@{latest}",
                summary="journal reference only — body withheld",
                hash_excerpt=_hash_excerpt({"source": source_key, "latest": latest}),
            )
        )

    for source_key in refresh.missing_sources:
        refs.append(
            EvidenceRef(
                ref_id=f"missing:{source_key}",
                kind="missing_source",
                source=source_key,
                summary="source not fresh in current window",
                hash_excerpt=_hash_excerpt({"missing": source_key}),
            )
        )

    refs.append(
        EvidenceRef(
            ref_id="refresh:meta",
            kind="refresh_meta",
            source="context_refresh",
            summary=(
                f"confidence={refresh.confidence}; "
                f"sukoon={refresh.sukoon_capacity}; "
                f"found={len(refresh.sources_found)}"
            ),
            hash_excerpt=_hash_excerpt(refresh.to_dict()),
        )
    )
    return refs


def contains_journal_egress(pack: list[EvidenceRef], *, forbidden_text: str) -> bool:
    """Return True if forbidden journal body text leaked into the evidence pack."""
    needle = forbidden_text.strip()
    if not needle:
        return False
    pattern = re.compile(re.escape(needle), re.IGNORECASE)
    for ref in pack:
        if pattern.search(ref.summary):
            return True
        if ref.source and pattern.search(ref.source):
            return True
    return False
