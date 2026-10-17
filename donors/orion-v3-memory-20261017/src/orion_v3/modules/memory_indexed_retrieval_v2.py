"""Experimental read-only retrieval sidecar over explicit caller-approved memory projections.

Never writes canonical ORION memory. The index is disposable, rebuildable and
cannot confer authority. Caller MUST enforce permissions and validate returned
IDs through the canonical project/provenance/supersession path.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import sqlite3
from contextlib import closing
from typing import Iterable

@dataclass(frozen=True)
class IndexedRecord:
    memory_id: str
    project_id: str
    content: str
    source_ref: str
    active: bool = True

@dataclass(frozen=True)
class IndexedHit:
    memory_id: str
    project_id: str
    source_ref: str
    score: float

class IndexedRetrievalV2:
    """Candidate IDs only; NEVER returns authoritative prompt context."""

    def __init__(self, sidecar_path: str | Path):
        self.path = Path(sidecar_path)
        if not self.path.parent.is_dir():
            raise ValueError("Sidecar parent directory must already exist")
        self._create()

    def _connect(self):
        conn = sqlite3.connect(str(self.path), timeout=10)
        conn.execute("PRAGMA busy_timeout=10000")
        return conn

    def _create(self):
        with closing(self._connect()) as conn, conn:
            conn.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS indexed_memory USING fts5(
                memory_id UNINDEXED, project_id UNINDEXED, source_ref UNINDEXED,
                content, tokenize='unicode61 remove_diacritics 2'
            )""")

    def rebuild(self, records: Iterable[IndexedRecord]) -> int:
        """Replace ONLY this derived index, never canonical data."""
        validated = []
        ids = set()
        for r in records:
            if not r.active:
                continue
            if not r.memory_id or not r.project_id or not r.source_ref:
                raise ValueError("Every indexed row requires ID, project and provenance")
            if r.memory_id in ids:
                raise ValueError("Duplicate canonical memory ID")
            ids.add(r.memory_id)
            validated.append((r.memory_id, r.project_id, r.source_ref, r.content))
        with closing(self._connect()) as conn, conn:
            conn.execute("DELETE FROM indexed_memory")
            conn.executemany(
                "INSERT INTO indexed_memory(memory_id,project_id,source_ref,content) VALUES (?,?,?,?)",
                validated,
            )
        return len(validated)

    def candidates(self, query: str, *, project_id: str, limit: int = 12) -> list[IndexedHit]:
        """Fail-closed on missing project; no cross-project or wildcard mode."""
        if not project_id or not project_id.strip():
            raise ValueError("Explicit project_id required")
        terms = query.strip().split()
        if not terms or len(terms) > 24 or len(query) > 2000:
            return []
        # FTS5 safely quotes individual terms: never interpret caller syntax.
        expression = " OR ".join('"' + token.replace('"', '""') + '"' for token in terms)
        with closing(self._connect()) as conn, conn:
            rows = conn.execute(
                """SELECT memory_id,project_id,source_ref,bm25(indexed_memory)
                   FROM indexed_memory WHERE indexed_memory MATCH ?
                   AND project_id = ? ORDER BY bm25(indexed_memory) LIMIT ?""",
                (expression, project_id, min(max(1, int(limit)), 12)),
            ).fetchall()
        return [IndexedHit(*row) for row in rows]
