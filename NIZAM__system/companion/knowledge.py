from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from .contracts import KnowledgeClaim

TOKEN_RE = re.compile(r"[a-z0-9_]+")


def _fts_query(text: str) -> str:
    tokens = [token for token in TOKEN_RE.findall(text.lower()) if len(token) > 2]
    if not tokens:
        return text
    return " OR ".join(f'"{token}"' for token in tokens)


class KnowledgeStore:
    def __init__(self, path: Path) -> None:
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS claims (
              claim_id TEXT PRIMARY KEY, claim TEXT NOT NULL, source_title TEXT NOT NULL,
              source_url TEXT NOT NULL, published_at TEXT, retrieved_at TEXT NOT NULL,
              reliability TEXT NOT NULL, summary TEXT NOT NULL, implications TEXT NOT NULL,
              privacy_class TEXT NOT NULL, supersedes TEXT
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS claims_fts USING fts5(
              claim_id UNINDEXED, claim, source_title, summary, implications
            );
            """
        )

    def add(self, claim: KnowledgeClaim) -> None:
        values = claim.to_dict()
        columns = ", ".join(values)
        marks = ", ".join("?" for _ in values)
        self.db.execute(
            f"INSERT OR REPLACE INTO claims ({columns}) VALUES ({marks})",
            tuple(values.values()),
        )
        self.db.execute("DELETE FROM claims_fts WHERE claim_id = ?", (claim.claim_id,))
        self.db.execute(
            "INSERT INTO claims_fts VALUES (?, ?, ?, ?, ?)",
            (claim.claim_id, claim.claim, claim.source_title, claim.summary, claim.implications),
        )
        self.db.commit()

    def search(self, query: str, *, limit: int = 5) -> list[dict[str, object]]:
        rows = self.db.execute(
            """
            SELECT c.*, bm25(claims_fts) AS rank
            FROM claims_fts JOIN claims c USING (claim_id)
            WHERE claims_fts MATCH ?
            ORDER BY rank LIMIT ?
            """,
            (_fts_query(query), limit),
        ).fetchall()
        return [dict(row) for row in rows]

    def close(self) -> None:
        self.db.close()
