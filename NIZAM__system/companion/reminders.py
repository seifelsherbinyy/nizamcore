from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


FATWA_PATTERNS = (
    re.compile(r"\b(?:fatwa|ruling|haram|halal|wajib|fard)\b", re.I),
    re.compile(r"\b(?:you must|it is obligatory|forbidden for you)\b", re.I),
)

DISPUTED_AS_SETTLED = re.compile(
    r"\b(?:consensus|unanimous|definitely authentic|undisputed)\b", re.I
)

DEFAULT_CORPUS = Path(__file__).resolve().parent / "fixtures" / "approved_reminders.json"


@dataclass(frozen=True)
class ReminderSource:
    source_id: str
    source_type: str
    reference: str
    text: str
    authenticity: str
    approved: bool = True


def load_corpus(path: Path = DEFAULT_CORPUS) -> dict[str, ReminderSource]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    corpus: dict[str, ReminderSource] = {}
    for row in payload:
        source = ReminderSource(**row)
        corpus[source.source_id] = source
    return corpus


def validate_sourced_reminder(
    message: str,
    source_ids: tuple[str, ...],
    *,
    corpus: dict[str, ReminderSource] | None = None,
) -> tuple[bool, str]:
    """Validate a constrained sourced reminder before staging delivery."""
    if not source_ids:
        return False, "missing_citation"
    corpus = corpus or load_corpus()
    for pattern in FATWA_PATTERNS:
        if pattern.search(message):
            return False, "fatwa_language"
    for source_id in source_ids:
        source = corpus.get(source_id)
        if source is None or not source.approved:
            return False, "unapproved_source"
        if source.authenticity == "disputed" and DISPUTED_AS_SETTLED.search(message):
            return False, "disputed_presented_as_settled"
        if source.authenticity == "unknown":
            return False, "unknown_authenticity"
    return True, "valid"
