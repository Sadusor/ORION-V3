from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import re
import sqlite3
import threading
import time
from contextlib import closing
from typing import Any

from .memory_candidate_queue import CanonicalMemoryCandidateQueue, OWNER_SCOPE

SCHEMA = "orion.canonical-memory-review/1"
DECISION_SCHEMA = "orion.memory-decision/1"
MEMORY_SCHEMA = "orion.canonical-memory/1"
RULE_ID = "owner-explicit-review-v1"

_ALLOWED = {"promote", "reject", "defer"}
_TERMINAL = {"promote", "reject"}

_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----", re.I),
    re.compile(r"\bpassword\s*[:=]\s*\S+", re.I),
    re.compile(r"\bapi[_ -]?key\s*[:=]\s*\S+", re.I),
    re.compile(r"\bsecret\s*[:=]\s*\S+", re.I),
    re.compile(r"\bauthorization\s*:\s*bearer\s+\S+", re.I),
    re.compile(r"\btoken\s*[:=]\s*\S{8,}", re.I),
)


class MemoryReviewError(RuntimeError):
    pass


def _clean(value: Any, limit: int) -> str:
    return str(value or "").strip()[:limit]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(str(text).encode("utf-8"))


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _secret_risks(text: str) -> list[str]:
    flags: list[str] = []
    for pattern in _SECRET_PATTERNS:
        if pattern.search(str(text or "")):
            flags.append("possible_secret")
            break
    return flags


class CanonicalMemoryReviewPromotion:
    """Append-only owner review + canonical promotion boundary.

    The candidate queue remains immutable. This module appends owner decisions
    and, on PROMOTE only, creates an immutable canonical-memory record from the
    exact candidate snapshot.

    V1 intentionally does not support supersession or editing. Terminal decisions
    cannot be changed; corrections are a later module.
    """

    def __init__(
        self,
        path: pathlib.Path,
        candidates: CanonicalMemoryCandidateQueue,
    ):
        self.path = pathlib.Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.candidates = candidates
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
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS decision_events(
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_id TEXT NOT NULL UNIQUE,
                    schema TEXT NOT NULL,
                    candidate_id TEXT NOT NULL,
                    candidate_content_sha256 TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    rule_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    owner_scope TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    source_ref TEXT NOT NULL,
                    trust_origin TEXT NOT NULL,
                    trust_tier TEXT NOT NULL,
                    candidate_snapshot_json TEXT NOT NULL,
                    decided_at_ms INTEGER NOT NULL,
                    prev_event_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL UNIQUE
                );

                CREATE TABLE IF NOT EXISTS canonical_memories(
                    memory_id TEXT PRIMARY KEY,
                    schema TEXT NOT NULL,
                    candidate_id TEXT NOT NULL UNIQUE,
                    content TEXT NOT NULL,
                    content_sha256 TEXT NOT NULL,
                    owner_scope TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    classification TEXT NOT NULL,
                    trust_origin TEXT NOT NULL,
                    trust_tier TEXT NOT NULL,
                    source_ref TEXT NOT NULL,
                    candidate_snapshot_json TEXT NOT NULL,
                    promoted_decision_id TEXT NOT NULL UNIQUE,
                    promoted_event_hash TEXT NOT NULL UNIQUE,
                    created_at_ms INTEGER NOT NULL,
                    status TEXT NOT NULL
                );

                CREATE TRIGGER IF NOT EXISTS decision_events_no_update
                BEFORE UPDATE ON decision_events
                BEGIN
                    SELECT RAISE(ABORT, 'decision_events are append-only');
                END;

                CREATE TRIGGER IF NOT EXISTS decision_events_no_delete
                BEFORE DELETE ON decision_events
                BEGIN
                    SELECT RAISE(ABORT, 'decision_events are append-only');
                END;

                CREATE TRIGGER IF NOT EXISTS canonical_memories_no_update
                BEFORE UPDATE ON canonical_memories
                BEGIN
                    SELECT RAISE(ABORT, 'canonical_memories are immutable in V1');
                END;

                CREATE TRIGGER IF NOT EXISTS canonical_memories_no_delete
                BEFORE DELETE ON canonical_memories
                BEGIN
                    SELECT RAISE(ABORT, 'canonical_memories are immutable in V1');
                END;
                """
            )

    def _candidate(self, candidate_id: str) -> dict[str, Any]:
        candidate_id = _clean(candidate_id, 120)
        if not candidate_id:
            raise MemoryReviewError("candidate_id is required.")
        listed = self.candidates.list()
        candidate = next(
            (copy.deepcopy(x) for x in listed.get("candidates", []) if x.get("candidate_id") == candidate_id),
            None,
        )
        if not candidate:
            raise MemoryReviewError("Memory candidate was not found.")
        if candidate.get("owner_scope") != OWNER_SCOPE:
            raise MemoryReviewError("Candidate owner scope is not supported.")
        return candidate

    def candidates_view(self) -> dict[str, Any]:
        base = self.candidates.list()
        latest = self._latest_by_candidate()
        memories = {
            x["candidate_id"]: x
            for x in self.list_canonical().get("memories", [])
        }
        out = []
        counts = {"pending": 0, "defer": 0, "promote": 0, "reject": 0}
        for item in base.get("candidates", []):
            c = copy.deepcopy(item)
            event = latest.get(str(c.get("candidate_id") or ""))
            if event:
                decision = event["decision"]
                c["decision"] = decision
                c["decision_reason"] = event["reason"]
                c["decision_rule_id"] = event["rule_id"]
                c["decided_at"] = int(event["decided_at_ms"])
                c["decision_id"] = event["decision_id"]
                c["decision_event_hash"] = event["event_hash"]
                c["status"] = {
                    "defer": "deferred",
                    "promote": "promoted",
                    "reject": "rejected",
                }[decision]
                c["canonical"] = decision == "promote"
                c["authority"] = "canonical_context" if decision == "promote" else "candidate_only"
                if decision == "promote":
                    c["durable_memory_id"] = memories.get(c["candidate_id"], {}).get("memory_id", "")
            else:
                c["decision"] = "pending"
                c["status"] = "pending"
                c["canonical"] = False
                c["authority"] = "candidate_only"
            counts[c["decision"]] = counts.get(c["decision"], 0) + 1
            out.append(c)

        return {
            "schema": SCHEMA,
            "owner_scope": OWNER_SCOPE,
            "candidates": out,
            "count": len(out),
            "pending_count": counts.get("pending", 0),
            "deferred_count": counts.get("defer", 0),
            "promoted_count": counts.get("promote", 0),
            "rejected_count": counts.get("reject", 0),
            "canonical_memory_written": bool(counts.get("promote", 0)),
        }

    def decide(
        self,
        *,
        candidate_id: str,
        decision: str,
        expected_content_sha256: str,
        owner_scope: str = OWNER_SCOPE,
    ) -> dict[str, Any]:
        decision = _clean(decision, 20).lower()
        if decision not in _ALLOWED:
            raise MemoryReviewError("decision must be promote, reject, or defer.")
        if _clean(owner_scope, 120) != OWNER_SCOPE:
            raise MemoryReviewError("Unsupported owner_scope.")

        candidate = self._candidate(candidate_id)
        expected = _clean(expected_content_sha256, 64).lower()
        actual = str(candidate.get("content_sha256") or "").lower()
        if not expected or expected != actual:
            raise MemoryReviewError("Candidate content hash mismatch; refresh review state.")

        if decision == "promote":
            risks = _secret_risks(str(candidate.get("content") or ""))
            if risks:
                raise MemoryReviewError(
                    "Promotion blocked: candidate appears to contain secret material."
                )

        now_ms = int(time.time() * 1000)
        reason = "owner_explicit_review"
        snapshot_json = _canonical_json(candidate)

        with self._lock, closing(self._connect()) as con:
            con.execute("BEGIN IMMEDIATE")
            try:
                latest = con.execute(
                    "SELECT * FROM decision_events WHERE candidate_id=? "
                    "ORDER BY seq DESC LIMIT 1",
                    (candidate["candidate_id"],),
                ).fetchone()

                if latest is not None:
                    latest = dict(latest)
                    latest_decision = str(latest["decision"])
                    if latest_decision in _TERMINAL:
                        if latest_decision != decision:
                            raise MemoryReviewError(
                                "Candidate already has a terminal owner decision."
                            )
                        con.rollback()
                        return self._decision_result(
                            candidate,
                            latest,
                            created=False,
                            memory=self._memory_for_candidate(candidate["candidate_id"]),
                        )
                    if latest_decision == "defer" and decision == "defer":
                        con.rollback()
                        return self._decision_result(
                            candidate,
                            latest,
                            created=False,
                            memory=None,
                        )

                previous = con.execute(
                    "SELECT event_hash FROM decision_events ORDER BY seq DESC LIMIT 1"
                ).fetchone()
                prev_hash = str(previous["event_hash"]) if previous else ""

                event_payload = {
                    "schema": DECISION_SCHEMA,
                    "candidate_id": candidate["candidate_id"],
                    "candidate_content_sha256": actual,
                    "decision": decision,
                    "rule_id": RULE_ID,
                    "reason": reason,
                    "owner_scope": OWNER_SCOPE,
                    "project_id": str(candidate.get("project_id") or ""),
                    "source_ref": str(candidate.get("source_ref") or ""),
                    "trust_origin": str(candidate.get("trust_origin") or ""),
                    "trust_tier": str(candidate.get("trust_tier") or ""),
                    "candidate_snapshot_sha256": _sha256_text(snapshot_json),
                    "decided_at_ms": now_ms,
                    "prev_event_hash": prev_hash,
                }
                event_hash = _sha256_text(_canonical_json(event_payload))
                decision_id = "md_" + event_hash[:24]

                con.execute(
                    """
                    INSERT INTO decision_events(
                        decision_id,schema,candidate_id,candidate_content_sha256,
                        decision,rule_id,reason,owner_scope,project_id,source_ref,
                        trust_origin,trust_tier,candidate_snapshot_json,decided_at_ms,
                        prev_event_hash,event_hash
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        decision_id,
                        DECISION_SCHEMA,
                        candidate["candidate_id"],
                        actual,
                        decision,
                        RULE_ID,
                        reason,
                        OWNER_SCOPE,
                        str(candidate.get("project_id") or ""),
                        str(candidate.get("source_ref") or ""),
                        str(candidate.get("trust_origin") or ""),
                        str(candidate.get("trust_tier") or ""),
                        snapshot_json,
                        now_ms,
                        prev_hash,
                        event_hash,
                    ),
                )

                memory = None
                if decision == "promote":
                    memory_id = "cm_" + _sha256_text(
                        "|".join(
                            [
                                OWNER_SCOPE,
                                candidate["candidate_id"],
                                actual,
                                decision_id,
                            ]
                        )
                    )[:24]
                    con.execute(
                        """
                        INSERT INTO canonical_memories(
                            memory_id,schema,candidate_id,content,content_sha256,
                            owner_scope,project_id,classification,trust_origin,trust_tier,
                            source_ref,candidate_snapshot_json,promoted_decision_id,
                            promoted_event_hash,created_at_ms,status
                        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        """,
                        (
                            memory_id,
                            MEMORY_SCHEMA,
                            candidate["candidate_id"],
                            str(candidate.get("content") or ""),
                            actual,
                            OWNER_SCOPE,
                            str(candidate.get("project_id") or ""),
                            str(candidate.get("classification") or "conversation_recall"),
                            str(candidate.get("trust_origin") or ""),
                            str(candidate.get("trust_tier") or ""),
                            str(candidate.get("source_ref") or ""),
                            snapshot_json,
                            decision_id,
                            event_hash,
                            now_ms,
                            "active",
                        ),
                    )
                    memory = self._memory_public(
                        con.execute(
                            "SELECT * FROM canonical_memories WHERE memory_id=?",
                            (memory_id,),
                        ).fetchone()
                    )

                con.commit()
                event = con.execute(
                    "SELECT * FROM decision_events WHERE decision_id=?",
                    (decision_id,),
                ).fetchone()
                return self._decision_result(
                    candidate,
                    dict(event),
                    created=True,
                    memory=memory,
                )
            except Exception:
                con.rollback()
                raise

    def _latest_by_candidate(self) -> dict[str, dict[str, Any]]:
        with self._lock, closing(self._connect()) as con:
            rows = con.execute(
                """
                SELECT d.* FROM decision_events d
                JOIN (
                    SELECT candidate_id, MAX(seq) AS max_seq
                    FROM decision_events
                    GROUP BY candidate_id
                ) latest
                  ON latest.candidate_id=d.candidate_id AND latest.max_seq=d.seq
                """
            ).fetchall()
        return {str(row["candidate_id"]): dict(row) for row in rows}

    def _memory_for_candidate(self, candidate_id: str) -> dict[str, Any] | None:
        with self._lock, closing(self._connect()) as con:
            row = con.execute(
                "SELECT * FROM canonical_memories WHERE candidate_id=?",
                (candidate_id,),
            ).fetchone()
            return self._memory_public(row) if row is not None else None

    def list_canonical(self) -> dict[str, Any]:
        with self._lock, closing(self._connect()) as con:
            rows = con.execute(
                "SELECT * FROM canonical_memories ORDER BY created_at_ms DESC, memory_id DESC"
            ).fetchall()
            memories = [self._memory_public(row) for row in rows]
        return {
            "schema": "orion.canonical-memory-list/1",
            "owner_scope": OWNER_SCOPE,
            "authority": "context_only",
            "memories": memories,
            "count": len(memories),
        }

    def decisions(self) -> dict[str, Any]:
        with self._lock, closing(self._connect()) as con:
            rows = con.execute(
                "SELECT * FROM decision_events ORDER BY seq ASC"
            ).fetchall()
            events = [self._decision_public(dict(row)) for row in rows]
        return {
            "schema": "orion.memory-decision-log/1",
            "append_only": True,
            "events": events,
            "count": len(events),
        }

    def audit_chain(self) -> dict[str, Any]:
        with self._lock, closing(self._connect()) as con:
            rows = con.execute(
                "SELECT * FROM decision_events ORDER BY seq ASC"
            ).fetchall()

        prev = ""
        problems: list[str] = []
        for row in rows:
            r = dict(row)
            if r["prev_event_hash"] != prev:
                problems.append(f"seq {r['seq']}: prev hash mismatch")
            snapshot_sha = _sha256_text(r["candidate_snapshot_json"])
            payload = {
                "schema": r["schema"],
                "candidate_id": r["candidate_id"],
                "candidate_content_sha256": r["candidate_content_sha256"],
                "decision": r["decision"],
                "rule_id": r["rule_id"],
                "reason": r["reason"],
                "owner_scope": r["owner_scope"],
                "project_id": r["project_id"],
                "source_ref": r["source_ref"],
                "trust_origin": r["trust_origin"],
                "trust_tier": r["trust_tier"],
                "candidate_snapshot_sha256": snapshot_sha,
                "decided_at_ms": int(r["decided_at_ms"]),
                "prev_event_hash": r["prev_event_hash"],
            }
            expected = _sha256_text(_canonical_json(payload))
            if expected != r["event_hash"]:
                problems.append(f"seq {r['seq']}: event hash mismatch")
            prev = r["event_hash"]

        return {
            "schema": "orion.memory-decision-audit/1",
            "ok": not problems,
            "events": len(rows),
            "head_hash": prev,
            "problems": problems,
        }

    @staticmethod
    def _decision_public(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "decision_id": row["decision_id"],
            "schema": row["schema"],
            "candidate_id": row["candidate_id"],
            "candidate_content_sha256": row["candidate_content_sha256"],
            "decision": row["decision"],
            "rule_id": row["rule_id"],
            "reason": row["reason"],
            "owner_scope": row["owner_scope"],
            "project_id": row["project_id"],
            "source_ref": row["source_ref"],
            "trust_origin": row["trust_origin"],
            "trust_tier": row["trust_tier"],
            "decided_at_ms": int(row["decided_at_ms"]),
            "prev_event_hash": row["prev_event_hash"],
            "event_hash": row["event_hash"],
        }

    @staticmethod
    def _memory_public(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
        r = dict(row)
        return {
            "memory_id": r["memory_id"],
            "schema": r["schema"],
            "candidate_id": r["candidate_id"],
            "content": r["content"],
            "content_sha256": r["content_sha256"],
            "owner_scope": r["owner_scope"],
            "project_id": r["project_id"],
            "classification": r["classification"],
            "trust_origin": r["trust_origin"],
            "trust_tier": r["trust_tier"],
            "source_ref": r["source_ref"],
            "promoted_decision_id": r["promoted_decision_id"],
            "promoted_event_hash": r["promoted_event_hash"],
            "created_at_ms": int(r["created_at_ms"]),
            "status": r["status"],
            "canonical": True,
            "authority": "context_only",
        }

    @staticmethod
    def _decision_result(
        candidate: dict[str, Any],
        event: dict[str, Any],
        *,
        created: bool,
        memory: dict[str, Any] | None,
    ) -> dict[str, Any]:
        return {
            "ok": True,
            "created": created,
            "decision": CanonicalMemoryReviewPromotion._decision_public(event),
            "candidate_id": candidate["candidate_id"],
            "canonical_memory_written": memory is not None,
            "memory": memory,
        }
