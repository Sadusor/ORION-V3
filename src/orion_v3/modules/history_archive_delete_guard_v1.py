"""Stage C owner-delete replay guard (isolated prototype; not routed live).

A server-side SQLite tombstone ledger records authenticated owner deletion.
Client sync payloads are *not* authorization for deletion. The guard refuses
stale conversation/message replay and never mutates the frozen live store.
"""
from __future__ import annotations

import sqlite3
import threading
from contextlib import closing
from pathlib import Path


class DeletedConversationReplay(RuntimeError):
    pass


class OwnerDeleteLedgerV1:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        with closing(self._connect()) as db, db:
            db.execute("""CREATE TABLE IF NOT EXISTS owner_deletions(
                conversation_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                deleted_at_ms INTEGER NOT NULL CHECK(deleted_at_ms > 0)
            )""")

    def _connect(self):
        db = sqlite3.connect(str(self.path), timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def record_owner_delete(self, *, conversation_id: str, project_id: str,
                            deleted_at_ms: int, owner_authorized: bool = False):
        if not owner_authorized:
            raise PermissionError("Only authenticated owner delete may create a tombstone")
        if not conversation_id or not project_id or int(deleted_at_ms) <= 0:
            raise ValueError("Valid conversation, project and timestamp required")
        with self._lock, closing(self._connect()) as db, db:
            row = db.execute(
                "SELECT project_id FROM owner_deletions WHERE conversation_id=?",
                (conversation_id,)
            ).fetchone()
            if row is not None and row["project_id"] != project_id:
                raise DeletedConversationReplay("Conversation id owned by another project")
            db.execute("""INSERT INTO owner_deletions(conversation_id,project_id,deleted_at_ms)
                VALUES(?,?,?) ON CONFLICT(conversation_id) DO UPDATE SET
                deleted_at_ms=max(owner_deletions.deleted_at_ms,excluded.deleted_at_ms)""",
                (conversation_id, project_id, int(deleted_at_ms)))

    def reject_replays(self, payload: dict):
        """Reject entire incoming batch if a tombstoned conversation is referenced.

        This is deliberately stricter than filtering; the client must learn
        the tombstone before it can retry safely.
        """
        if not isinstance(payload, dict):
            raise ValueError("Expected sync payload")
        conversations = payload.get("conversations", [])
        messages = payload.get("messages", [])
        if not isinstance(conversations, list) or not isinstance(messages, list):
            raise ValueError("Expected sync arrays")
        ids = set()
        for c in conversations:
            if not isinstance(c, dict):
                raise ValueError("Invalid conversation")
            if c.get("id"):
                ids.add(str(c["id"]))
        for m in messages:
            if not isinstance(m, dict):
                raise ValueError("Invalid message")
            if m.get("conversation_id"):
                ids.add(str(m["conversation_id"]))
        if not ids:
            return
        with self._lock, closing(self._connect()) as db:
            for cid in ids:
                if db.execute(
                    "SELECT 1 FROM owner_deletions WHERE conversation_id=?", (cid,)
                ).fetchone():
                    raise DeletedConversationReplay(
                        "Owner-deleted conversation cannot be replayed via sync"
                    )

    def tombstones(self) -> list[dict]:
        with self._lock, closing(self._connect()) as db:
            return [dict(r) for r in db.execute(
                "SELECT conversation_id,project_id,deleted_at_ms "
                "FROM owner_deletions ORDER BY conversation_id"
            ).fetchall()]
