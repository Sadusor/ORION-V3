from __future__ import annotations

import hashlib
import json
import pathlib
import sqlite3
import threading
import time
from contextlib import closing
from typing import Any

from .chat_history import ChatHistoryStore

SCHEMA = "orion.memory-candidate-queue/1"
CANDIDATE_SCHEMA = "orion.memory-candidate/1"
OWNER_SCOPE = "owner:primary"
MAX_CANDIDATES = 500
MAX_CONTENT_CHARS = 8_000


class MemoryCandidateError(RuntimeError):
    pass


def _clean(value: Any, limit: int) -> str:
    return str(value or "").strip()[:limit]


def _sha256_text(text: str) -> str:
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def _trust_for_role(role: str) -> tuple[str, str]:
    if role == "assistant":
        return "derived", "assistant_prior_unverified"
    return "user", "owner_message_unverified"


class CanonicalMemoryCandidateQueue:
    """Owner-reviewed intake queue before canonical memory promotion.

    This module is deliberately NOT canonical memory.

    It may:
    - snapshot an exact existing chat message after an authenticated owner request;
    - store immutable provenance for later review;
    - list queued candidates.

    It may NOT:
    - promote/reject canonical memory;
    - rewrite or delete chat history;
    - infer candidates automatically;
    - accept arbitrary client-supplied candidate text;
    - grant authority, permissions, capabilities, or execution.
    """

    def __init__(self, path: pathlib.Path, history: ChatHistoryStore):
        self.path = pathlib.Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.history = history
        self._lock = threading.RLock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.path, timeout=5.0)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA foreign_keys=ON")
        return con

    def _init_db(self) -> None:
        with self._lock, closing(self._connect()) as con, con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS candidates(
                    candidate_id TEXT PRIMARY KEY,
                    schema TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_sha256 TEXT NOT NULL,
                    owner_scope TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    source_conversation_id TEXT NOT NULL,
                    source_message_id TEXT NOT NULL,
                    source_role TEXT NOT NULL,
                    source_message_source TEXT NOT NULL,
                    source_created_at_ms INTEGER NOT NULL,
                    source_ref TEXT NOT NULL,
                    trust_origin TEXT NOT NULL,
                    trust_tier TEXT NOT NULL,
                    classification TEXT NOT NULL,
                    reason_for_candidate TEXT NOT NULL,
                    state TEXT NOT NULL,
                    submitted_at_ms INTEGER NOT NULL
                )
                """
            )
            con.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_candidates_source "
                "ON candidates(owner_scope, source_type, source_message_id, content_sha256)"
            )

    def enqueue_chat_message(
        self,
        *,
        conversation_id: str,
        message_id: str,
        project_id: str | None = None,
        owner_scope: str = OWNER_SCOPE,
    ) -> dict[str, Any]:
        conversation_id = _clean(conversation_id, 120)
        message_id = _clean(message_id, 160)
        if not conversation_id or not message_id:
            raise MemoryCandidateError("conversation_id and message_id are required.")
        if _clean(owner_scope, 120) != OWNER_SCOPE:
            raise MemoryCandidateError("Unsupported owner_scope.")

        snap = self.history.snapshot()
        conversations = {
            str(c.get("id") or ""): c
            for c in snap.get("conversations", [])
            if isinstance(c, dict)
        }
        conv = conversations.get(conversation_id)
        if not conv:
            raise MemoryCandidateError("Source conversation was not found.")
        if bool(conv.get("deleted")):
            raise MemoryCandidateError("Deleted conversations cannot create memory candidates.")
        if bool(conv.get("archived")):
            raise MemoryCandidateError("Archived conversations cannot create memory candidates.")

        actual_project = _clean(conv.get("project_id"), 160)
        if project_id is not None and _clean(project_id, 160) != actual_project:
            raise MemoryCandidateError("Source project scope mismatch.")

        msg = next(
            (
                m
                for m in snap.get("messages", [])
                if isinstance(m, dict)
                and _clean(m.get("id"), 160) == message_id
                and _clean(m.get("conversation_id"), 120) == conversation_id
            ),
            None,
        )
        if not msg:
            raise MemoryCandidateError("Source message was not found.")

        role = _clean(msg.get("role"), 20).lower()
        if role not in {"user", "assistant"}:
            raise MemoryCandidateError("Only user/assistant chat messages can become candidates.")

        content = _clean(msg.get("text"), MAX_CONTENT_CHARS)
        if not content:
            raise MemoryCandidateError("Empty messages cannot become memory candidates.")

        content_hash = _sha256_text(content)
        trust_origin, trust_tier = _trust_for_role(role)
        source_ref = f"chat_history:{conversation_id}:{message_id}"
        candidate_id = "mc_" + _sha256_text(
            "|".join(
                [
                    OWNER_SCOPE,
                    "chat_message",
                    conversation_id,
                    message_id,
                    content_hash,
                ]
            )
        )[:24]
        now_ms = int(time.time() * 1000)

        row = {
            "candidate_id": candidate_id,
            "schema": CANDIDATE_SCHEMA,
            "content": content,
            "content_sha256": content_hash,
            "owner_scope": OWNER_SCOPE,
            "project_id": actual_project,
            "source_type": "chat_message",
            "source_conversation_id": conversation_id,
            "source_message_id": message_id,
            "source_role": role,
            "source_message_source": _clean(msg.get("source"), 80),
            "source_created_at_ms": int(msg.get("created_at_ms") or 0),
            "source_ref": source_ref,
            "trust_origin": trust_origin,
            "trust_tier": trust_tier,
            "classification": "conversation_recall",
            "reason_for_candidate": "owner_selected_exact_chat_message",
            "state": "pending",
            "submitted_at_ms": now_ms,
        }

        with self._lock, closing(self._connect()) as con, con:
            existing = con.execute(
                "SELECT * FROM candidates WHERE candidate_id=?",
                (candidate_id,),
            ).fetchone()
            if existing is None:
                con.execute(
                    """
                    INSERT INTO candidates(
                        candidate_id,schema,content,content_sha256,owner_scope,project_id,
                        source_type,source_conversation_id,source_message_id,source_role,
                        source_message_source,source_created_at_ms,source_ref,trust_origin,
                        trust_tier,classification,reason_for_candidate,state,submitted_at_ms
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    tuple(row.values()),
                )
                created = True
            else:
                row = dict(existing)
                created = False
            self._prune(con)

        return {
            "ok": True,
            "created": created,
            "candidate": self._public(row),
            "canonical_memory_written": False,
        }

    def _prune(self, con: sqlite3.Connection) -> None:
        rows = con.execute(
            "SELECT candidate_id FROM candidates ORDER BY submitted_at_ms DESC, candidate_id DESC"
        ).fetchall()
        for row in rows[MAX_CANDIDATES:]:
            con.execute("DELETE FROM candidates WHERE candidate_id=?", (row["candidate_id"],))

    def list(self) -> dict[str, Any]:
        with self._lock, closing(self._connect()) as con:
            rows = con.execute(
                "SELECT * FROM candidates ORDER BY submitted_at_ms DESC, candidate_id DESC LIMIT ?",
                (MAX_CANDIDATES,),
            ).fetchall()
            candidates = [self._public(dict(row)) for row in rows]
        return {
            "schema": SCHEMA,
            "owner_scope": OWNER_SCOPE,
            "canonical_memory_written": False,
            "candidates": candidates,
            "count": len(candidates),
            "limits": {"candidates": MAX_CANDIDATES},
        }

    @staticmethod
    def _public(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "candidate_id": row["candidate_id"],
            "schema": row["schema"],
            "content": row["content"],
            "content_sha256": row["content_sha256"],
            "owner_scope": row["owner_scope"],
            "project_id": row["project_id"],
            "task_id": "",
            "attempt_id": "",
            "source_event_id": "",
            "source_actor": "owner" if row["source_role"] == "user" else "assistant",
            "source_ref": row["source_ref"],
            "source_type": row["source_type"],
            "source_conversation_id": row["source_conversation_id"],
            "source_message_id": row["source_message_id"],
            "source_role": row["source_role"],
            "source_message_source": row["source_message_source"],
            "source_created_at_ms": int(row["source_created_at_ms"]),
            "trust_origin": row["trust_origin"],
            "trust_tier": row["trust_tier"],
            "classification": row["classification"],
            "reason_for_candidate": row["reason_for_candidate"],
            "confidence": None,
            "decision": "pending",
            "decision_reason": "Awaiting a separate owner-reviewed canonical promotion module.",
            "status": row["state"],
            "submitted_at": int(row["submitted_at_ms"]),
            "canonical": False,
            "authority": "candidate_only",
        }

    def export_json(self) -> str:
        return json.dumps(self.list(), ensure_ascii=False, separators=(",", ":"))
