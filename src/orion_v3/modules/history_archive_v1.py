"""ORION HistoryArchive V1 — independent long-term journal.

NOT wired into live traffic. No changes to ChatHistoryStore, canonical memory,
approval, verification, STOP or TheHands. Integrator must distinguish owner
deletion (tombstone) from automatic ChatHistoryStore pruning.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing
import threading
import time
from pathlib import Path
from typing import Any

SCHEMA = "orion.history-archive/1"
MAX_ARCHIVED_TEXT_CHARS = 2_000_000
VALID_ROLES = frozenset(("user", "assistant", "system"))


class ArchiveConflict(ValueError):
    pass


class HistoryArchiveV1:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        with self._lock, closing(self._connect()) as db, db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS conversations(
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    deleted_at_ms INTEGER
                );
                CREATE TABLE IF NOT EXISTS messages(
                    conversation_id TEXT NOT NULL,
                    message_id TEXT NOT NULL,
                    created_at_ms INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT '',
                    model_id TEXT NOT NULL DEFAULT '',
                    stored_at_ms INTEGER NOT NULL,
                    PRIMARY KEY(conversation_id,message_id)
                );
                CREATE INDEX IF NOT EXISTS idx_archive_project_time
                    ON messages(project_id,created_at_ms);
                CREATE INDEX IF NOT EXISTS idx_archive_conv_time
                    ON messages(conversation_id,created_at_ms,message_id);
            """)

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10.0)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA busy_timeout=10000")
        db.execute("PRAGMA foreign_keys=ON")
        return db

    @staticmethod
    def _key(value: Any, limit: int = 160) -> str:
        return str(value or "").strip()[:limit]

    def append_batch(self, conversations: list[dict[str, Any]],
                     messages: list[dict[str, Any]]) -> dict[str, int]:
        """Transactional idempotent append of original, untruncated sync fields.

        Explicit deleted=1 conversation rows are owner-delete signals only if
        the caller has VERIFIED that the client uses that flag for owner delete.
        This method deliberately does NOT interpret those flags automatically.
        """
        if not isinstance(conversations, list) or not isinstance(messages, list):
            raise ValueError("Expected conversation and message arrays")
        projects: dict[str, str] = {}
        for raw in conversations:
            if not isinstance(raw, dict):
                raise ValueError("Malformed conversation")
            cid = self._key(raw.get("id"), 120)
            if not cid:
                raise ValueError("Missing conversation id")
            projects[cid] = self._key(raw.get("project_id"), 160)
        normalized = []
        for raw in messages:
            if not isinstance(raw, dict):
                raise ValueError("Malformed message")
            cid = self._key(raw.get("conversation_id"), 120)
            mid = self._key(raw.get("id"), 160)
            role = self._key(raw.get("role"), 20).lower()
            message = str(raw.get("text") or "")
            if not cid or not mid or role not in VALID_ROLES or not message:
                raise ValueError("Missing or invalid archive message fields")
            if len(message) > MAX_ARCHIVED_TEXT_CHARS:
                raise ValueError("Message exceeds archive safety limit")
            ts = int(raw.get("created_at_ms") or 0)
            if ts <= 0:
                raise ValueError("Missing original message timestamp")
            project = self._key(raw.get("project_id"), 160) or projects.get(cid, "")
            normalized.append((cid, mid, ts, role, project, message,
                               self._key(raw.get("source"), 80),
                               self._key(raw.get("model_id"), 160)))
        inserted = 0
        now = int(time.time() * 1000)
        with self._lock, closing(self._connect()) as db, db:
            for cid, project in projects.items():
                existing = db.execute(
                    "SELECT project_id FROM conversations WHERE id=?", (cid,)
                ).fetchone()
                if existing is None:
                    db.execute("INSERT INTO conversations VALUES(?,?,NULL)",
                               (cid, project))
                elif project and existing["project_id"] and existing["project_id"] != project:
                    raise ArchiveConflict("Conversation project cannot change")
                elif project and not existing["project_id"]:
                    db.execute("UPDATE conversations SET project_id=? WHERE id=?",
                               (project, cid))
            for cid, mid, ts, role, project, message, source, model in normalized:
                row = db.execute(
                    "SELECT project_id,deleted_at_ms FROM conversations WHERE id=?",
                    (cid,)
                ).fetchone()
                if row is None:
                    db.execute("INSERT INTO conversations VALUES(?,?,NULL)",
                               (cid, project))
                elif row["deleted_at_ms"] is not None:
                    # A stale phone or desktop re-sync must never resurrect deleted data.
                    continue
                elif project and row["project_id"] and project != row["project_id"]:
                    raise ArchiveConflict("Message project does not match conversation")
                else:
                    project = project or row["project_id"]
                previous = db.execute(
                    "SELECT created_at_ms,role,project_id,text FROM messages "
                    "WHERE conversation_id=? AND message_id=?", (cid, mid)
                ).fetchone()
                if previous:
                    if (previous["created_at_ms"] != ts
                            or previous["role"] != role
                            or previous["text"] != message
                            or previous["project_id"] != project):
                        raise ArchiveConflict("Message id was replayed with changed content")
                    continue
                db.execute(
                    "INSERT INTO messages VALUES(?,?,?,?,?,?,?,?,?)",
                    (cid, mid, ts, role, project, message, source, model, now)
                )
                inserted += 1
        return {"inserted": inserted, "received": len(messages)}

    def delete_conversation(self, conversation_id: str, *, deleted_at_ms: int,
                            owner_delete_confirmed: bool = False) -> None:
        """Explicit owner delete; retain tombstone to prevent replay resurrection."""
        if not owner_delete_confirmed:
            raise PermissionError("Owner delete must be confirmed by the authenticated ingress")
        cid = self._key(conversation_id, 120)
        if not cid or int(deleted_at_ms) <= 0:
            raise ValueError("Conversation id and delete timestamp required")
        with self._lock, closing(self._connect()) as db, db:
            db.execute("INSERT OR IGNORE INTO conversations VALUES(?,?,?)",
                       (cid, "", deleted_at_ms))
            db.execute("UPDATE conversations SET deleted_at_ms=? WHERE id=?",
                       (deleted_at_ms, cid))
            db.execute("DELETE FROM messages WHERE conversation_id=?", (cid,))

    def query(self, *, project_id: str, conversation_id: str = "",
              contains: str = "", limit: int = 20) -> list[dict[str, Any]]:
        """Bounded scoped exact-text filtering; search index TBD by benchmark."""
        project = self._key(project_id, 160)
        if not project:
            raise ValueError("An explicit project scope is mandatory")
        limit = max(1, min(int(limit), 100))
        sql = ("SELECT m.* FROM messages m JOIN conversations c "
               "ON c.id=m.conversation_id "
               "WHERE c.deleted_at_ms IS NULL AND m.project_id=?")
        params: list[Any] = [project]
        if conversation_id:
            sql += " AND m.conversation_id=?"
            params.append(self._key(conversation_id, 120))
        if contains:
            sql += " AND instr(lower(m.text),lower(?))>0"
            params.append(str(contains)[:2000])
        sql += " ORDER BY m.created_at_ms DESC,m.message_id DESC LIMIT ?"
        params.append(limit)
        with self._lock, closing(self._connect()) as db, db:
            return [dict(row) for row in db.execute(sql, params).fetchall()]

    def export_conversation(self, *, project_id: str, conversation_id: str) -> bytes:
        cid = self._key(conversation_id, 120)
        project = self._key(project_id, 160)
        if not cid or not project:
            raise ValueError("Explicit project and conversation required")
        with self._lock, closing(self._connect()) as db, db:
            rows = [dict(r) for r in db.execute(
                "SELECT m.* FROM messages m JOIN conversations c "
                "ON c.id=m.conversation_id WHERE c.deleted_at_ms IS NULL "
                "AND m.project_id=? AND m.conversation_id=? "
                "ORDER BY m.created_at_ms,m.message_id",
                (project, cid)
            ).fetchall()]
        return json.dumps({"schema": SCHEMA, "conversation_id": cid,
                           "project_id": project, "messages": rows},
                          ensure_ascii=False, separators=(",", ":")).encode("utf-8")
