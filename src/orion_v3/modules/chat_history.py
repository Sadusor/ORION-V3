from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

SCHEMA = "orion.chat-history/1"
MAX_CONVERSATIONS = 200
MAX_MESSAGES_PER_CONVERSATION = 240
MAX_TEXT_CHARS = 100_000
MAX_TITLE_CHARS = 160


def _now_ms() -> int:
    return int(time.time() * 1000)


def _clean_text(value: Any, limit: int) -> str:
    return str(value or "").strip()[:limit]


def _int_bool(value: Any) -> int:
    return 1 if bool(value) else 0


class ChatHistoryStore:
    """Small, bounded, append-first conversation journal for PC/phone sync.

    Messages are immutable and deduplicated by message id. Conversation metadata uses
    last-write-wins by updated_at_ms. This keeps sync deterministic without giving the
    chat UI any execution authority.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.path, timeout=5)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=NORMAL")
        return con

    def _init_db(self) -> None:
        with self._lock, self._connect() as con:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL DEFAULT '',
                    project_id TEXT NOT NULL DEFAULT '',
                    pinned INTEGER NOT NULL DEFAULT 0,
                    archived INTEGER NOT NULL DEFAULT 0,
                    deleted INTEGER NOT NULL DEFAULT 0,
                    created_at_ms INTEGER NOT NULL,
                    updated_at_ms INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    text TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT '',
                    created_at_ms INTEGER NOT NULL,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
                );
                CREATE INDEX IF NOT EXISTS idx_history_conv_updated
                    ON conversations(updated_at_ms DESC);
                CREATE INDEX IF NOT EXISTS idx_history_msg_conv_created
                    ON messages(conversation_id, created_at_ms ASC);
                """
            )

    def _normalize_conversation(self, raw: dict[str, Any]) -> dict[str, Any] | None:
        cid = _clean_text(raw.get("id"), 120)
        if not cid:
            return None
        created = int(raw.get("created_at_ms") or _now_ms())
        updated = int(raw.get("updated_at_ms") or created)
        return {
            "id": cid,
            "title": _clean_text(raw.get("title"), MAX_TITLE_CHARS),
            "project_id": _clean_text(raw.get("project_id"), 160),
            "pinned": _int_bool(raw.get("pinned")),
            "archived": _int_bool(raw.get("archived")),
            "deleted": _int_bool(raw.get("deleted")),
            "created_at_ms": created,
            "updated_at_ms": updated,
        }

    def _normalize_message(self, raw: dict[str, Any]) -> dict[str, Any] | None:
        mid = _clean_text(raw.get("id"), 160)
        cid = _clean_text(raw.get("conversation_id"), 120)
        role = _clean_text(raw.get("role"), 20).lower()
        text = _clean_text(raw.get("text"), MAX_TEXT_CHARS)
        if not mid or not cid or role not in {"user", "assistant", "system"} or not text:
            return None
        return {
            "id": mid,
            "conversation_id": cid,
            "role": role,
            "text": text,
            "source": _clean_text(raw.get("source"), 80),
            "created_at_ms": int(raw.get("created_at_ms") or _now_ms()),
        }

    def sync(self, payload: dict[str, Any] | None) -> dict[str, Any]:
        payload = payload if isinstance(payload, dict) else {}
        conversations = payload.get("conversations") if isinstance(payload.get("conversations"), list) else []
        messages = payload.get("messages") if isinstance(payload.get("messages"), list) else []
        with self._lock, self._connect() as con:
            for raw in conversations[:MAX_CONVERSATIONS * 2]:
                if not isinstance(raw, dict):
                    continue
                c = self._normalize_conversation(raw)
                if not c:
                    continue
                row = con.execute("SELECT updated_at_ms FROM conversations WHERE id=?", (c["id"],)).fetchone()
                if row is None:
                    con.execute(
                        "INSERT INTO conversations(id,title,project_id,pinned,archived,deleted,created_at_ms,updated_at_ms) VALUES(?,?,?,?,?,?,?,?)",
                        tuple(c[k] for k in ("id", "title", "project_id", "pinned", "archived", "deleted", "created_at_ms", "updated_at_ms")),
                    )
                elif c["updated_at_ms"] >= int(row["updated_at_ms"]):
                    con.execute(
                        "UPDATE conversations SET title=?,project_id=?,pinned=?,archived=?,deleted=?,created_at_ms=min(created_at_ms,?),updated_at_ms=? WHERE id=?",
                        (c["title"], c["project_id"], c["pinned"], c["archived"], c["deleted"], c["created_at_ms"], c["updated_at_ms"], c["id"]),
                    )

            for raw in messages[: MAX_CONVERSATIONS * MAX_MESSAGES_PER_CONVERSATION * 2]:
                if not isinstance(raw, dict):
                    continue
                m = self._normalize_message(raw)
                if not m:
                    continue
                exists = con.execute("SELECT 1 FROM conversations WHERE id=?", (m["conversation_id"],)).fetchone()
                if exists is None:
                    ts = m["created_at_ms"]
                    con.execute(
                        "INSERT OR IGNORE INTO conversations(id,title,project_id,pinned,archived,deleted,created_at_ms,updated_at_ms) VALUES(?,?,?,?,?,?,?,?)",
                        (m["conversation_id"], "", "", 0, 0, 0, ts, ts),
                    )
                con.execute(
                    "INSERT OR IGNORE INTO messages(id,conversation_id,role,text,source,created_at_ms) VALUES(?,?,?,?,?,?)",
                    (m["id"], m["conversation_id"], m["role"], m["text"], m["source"], m["created_at_ms"]),
                )
                con.execute(
                    "UPDATE conversations SET updated_at_ms=max(updated_at_ms,?) WHERE id=?",
                    (m["created_at_ms"], m["conversation_id"]),
                )
            self._prune(con)
        return self.snapshot()

    def _prune(self, con: sqlite3.Connection) -> None:
        rows = con.execute(
            "SELECT id FROM conversations ORDER BY pinned DESC, updated_at_ms DESC"
        ).fetchall()
        for row in rows[MAX_CONVERSATIONS:]:
            con.execute("DELETE FROM messages WHERE conversation_id=?", (row["id"],))
            con.execute("DELETE FROM conversations WHERE id=?", (row["id"],))

        for row in con.execute("SELECT id FROM conversations").fetchall():
            ids = con.execute(
                "SELECT id FROM messages WHERE conversation_id=? ORDER BY created_at_ms DESC LIMIT -1 OFFSET ?",
                (row["id"], MAX_MESSAGES_PER_CONVERSATION),
            ).fetchall()
            if ids:
                con.executemany("DELETE FROM messages WHERE id=?", [(x["id"],) for x in ids])

    def snapshot(self) -> dict[str, Any]:
        with self._lock, self._connect() as con:
            conversations = [dict(row) for row in con.execute(
                "SELECT id,title,project_id,pinned,archived,deleted,created_at_ms,updated_at_ms FROM conversations ORDER BY pinned DESC, updated_at_ms DESC LIMIT ?",
                (MAX_CONVERSATIONS,),
            ).fetchall()]
            ids = [c["id"] for c in conversations]
            messages: list[dict[str, Any]] = []
            if ids:
                marks = ",".join("?" for _ in ids)
                messages = [dict(row) for row in con.execute(
                    f"SELECT id,conversation_id,role,text,source,created_at_ms FROM messages WHERE conversation_id IN ({marks}) ORDER BY created_at_ms ASC",
                    ids,
                ).fetchall()]
            return {
                "schema": SCHEMA,
                "conversations": conversations,
                "messages": messages,
                "limits": {
                    "conversations": MAX_CONVERSATIONS,
                    "messages_per_conversation": MAX_MESSAGES_PER_CONVERSATION,
                },
            }

    def export_json(self) -> str:
        return json.dumps(self.snapshot(), ensure_ascii=False, separators=(",", ":"))
