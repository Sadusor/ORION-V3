"""Experimental lossless chat-history store. NOT wired to product_server.

Separate candidate only. Never open the owner's production chat DB with this
module before a reviewed migration/activation gate.
"""
from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from threading import RLock

SCHEMA = "orion.chat-history/1"


class LosslessHistoryCandidate:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        with closing(self._connect()) as db, db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                  id TEXT PRIMARY KEY, title TEXT NOT NULL DEFAULT '',
                  project_id TEXT NOT NULL DEFAULT '', pinned INTEGER NOT NULL DEFAULT 0,
                  archived INTEGER NOT NULL DEFAULT 0, deleted INTEGER NOT NULL DEFAULT 0,
                  created_at_ms INTEGER NOT NULL, updated_at_ms INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                  id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL,
                  role TEXT NOT NULL, text TEXT NOT NULL, source TEXT NOT NULL DEFAULT '',
                  created_at_ms INTEGER NOT NULL
                );
            """)

    def _connect(self):
        return sqlite3.connect(self.path, timeout=5)

    def sync(self, payload: dict) -> dict:
        """Merge using stable IDs. Deletions stay monotonic in this candidate.

        Reject malformed batches transactionally. No silent trimming, pruning
        or conflict resurrection. Metadata timestamp ties preserve the existing
        value, unlike the legacy Python >= behavior.
        """
        if not isinstance(payload, dict):
            raise ValueError("payload must be object")
        conversations, messages = payload.get("conversations", []), payload.get("messages", [])
        if not isinstance(conversations, list) or not isinstance(messages, list):
            raise ValueError("conversations/messages must be arrays")
        with self._lock, closing(self._connect()) as db, db:
            for c in conversations:
                if not isinstance(c, dict) or not isinstance(c.get("id"), str) or not c["id"]:
                    raise ValueError("invalid conversation")
                incoming_deleted = 1 if c.get("deleted") else 0
                ts = int(c["updated_at_ms"])
                prior = db.execute(
                    "SELECT updated_at_ms,deleted FROM conversations WHERE id=?", (c["id"],)
                ).fetchone()
                if prior is None:
                    db.execute(
                        "INSERT INTO conversations VALUES (?,?,?,?,?,?,?,?)",
                        (c["id"], str(c.get("title", "")), str(c.get("project_id", "")),
                         int(bool(c.get("pinned"))), int(bool(c.get("archived"))),
                         incoming_deleted, int(c.get("created_at_ms", ts)), ts),
                    )
                elif ts > prior[0]:
                    db.execute(
                        """UPDATE conversations SET title=?,project_id=?,pinned=?,
                        archived=?,deleted=?,updated_at_ms=? WHERE id=?""",
                        (str(c.get("title", "")), str(c.get("project_id", "")),
                         int(bool(c.get("pinned"))), int(bool(c.get("archived"))),
                         int(bool(prior[1] or incoming_deleted)), ts, c["id"]),
                    )
                elif incoming_deleted and not prior[1]:
                    db.execute("UPDATE conversations SET deleted=1 WHERE id=?", (c["id"],))
            for m in messages:
                if (not isinstance(m, dict) or not isinstance(m.get("id"), str)
                    or not m["id"] or not isinstance(m.get("conversation_id"), str)
                    or not m["conversation_id"] or m.get("role") not in
                    ("user", "assistant", "system") or not isinstance(m.get("text"), str)
                    or not m["text"]):
                    raise ValueError("invalid message")
                if not db.execute("SELECT 1 FROM conversations WHERE id=?",
                                  (m["conversation_id"],)).fetchone():
                    raise ValueError("message references unknown conversation")
                db.execute(
                    "INSERT OR IGNORE INTO messages VALUES (?,?,?,?,?,?)",
                    (m["id"], m["conversation_id"], m["role"], m["text"],
                     str(m.get("source", "")), int(m["created_at_ms"])),
                )
        return self.snapshot()

    def snapshot(self) -> dict:
        with self._lock, closing(self._connect()) as db:
            db.row_factory = sqlite3.Row
            return {
                "schema": SCHEMA,
                "conversations": [dict(r) for r in db.execute(
                    "SELECT * FROM conversations ORDER BY pinned DESC,updated_at_ms DESC,id"
                )],
                "messages": [dict(r) for r in db.execute(
                    "SELECT * FROM messages ORDER BY created_at_ms,id"
                )],
            }

    def visible(self, limit=50) -> list[dict]:
        """Presentation limit only; never deletes persisted history."""
        return [c for c in self.snapshot()["conversations"]
                if not c["deleted"] and not c["archived"]][:limit]
