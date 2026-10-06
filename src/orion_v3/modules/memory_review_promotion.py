from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import re
import secrets
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
REVIEW_TICKET_TTL_SECONDS = 90

_ALLOWED = {"promote", "reject", "defer", "revoke"}
_TERMINAL = {"reject", "revoke"}

_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----", re.I),
    re.compile(r"\bpassword\s*[:=]\s*\S+", re.I),
    re.compile(r"\bapi[_ -]?key\s*[:=]\s*\S+", re.I),
    re.compile(r"\bsecret\s*[:=]\s*\S+", re.I),
    re.compile(r"\bauthorization\s*:\s*bearer\s+\S+", re.I),
    re.compile(r"\btoken\s*[:=]\s*\S{8,}", re.I),
)

_CANONICAL_INJECTION_PATTERNS = (
    re.compile(r"\bignore\s+(?:all\s+|any\s+)?previous\s+instructions?\b", re.I),
    re.compile(r"\bignore\s+(?:the\s+)?(?:system|developer)\s+(?:message|prompt|instructions?)\b", re.I),
    re.compile(r"\byou\s+are\s+now\b", re.I),
    re.compile(r"\bfollow\s+these\s+instructions?\b", re.I),
    re.compile(r"\boverride\s+(?:the\s+)?(?:system|developer|safety|policy)\b", re.I),
    re.compile(r"\breveal\s+(?:the\s+)?(?:system|developer)\s+(?:message|prompt)\b", re.I),
    re.compile(r"\bbypass\s+(?:approval|approvals|policy|safety|verifier)\b", re.I),
    re.compile(r"\balways\s+approve\b", re.I),
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


def _canonical_risks(text: str) -> list[str]:
    flags: list[str] = []
    if any(pattern.search(str(text or "")) for pattern in _SECRET_PATTERNS):
        flags.append("possible_secret")
    if any(pattern.search(str(text or "")) for pattern in _CANONICAL_INJECTION_PATTERNS):
        flags.append("instruction_like")
    return flags


class CanonicalMemoryReviewPromotion:
    """Owner-only durable canonical-memory write boundary.

    Candidate Queue remains frozen and immutable. This module adds:
    - one-time, short-lived server review tickets;
    - append-only owner decision events;
    - immutable canonical records on PROMOTE;
    - append-only REVOKE instead of deleting/editing canonical records.

    Canonical Memory remains context only. It never authorizes execution.
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
        self._review_tickets: dict[str, dict[str, Any]] = {}
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
                    event_index INTEGER NOT NULL UNIQUE,
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
                    actor_fingerprint TEXT NOT NULL,
                    review_ticket_sha256 TEXT NOT NULL,
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
            (
                copy.deepcopy(x)
                for x in listed.get("candidates", [])
                if x.get("candidate_id") == candidate_id
            ),
            None,
        )
        if not candidate:
            raise MemoryReviewError("Memory candidate was not found.")
        if candidate.get("owner_scope") != OWNER_SCOPE:
            raise MemoryReviewError("Candidate owner scope is not supported.")
        return candidate

    def _validate_transition(
        self,
        candidate: dict[str, Any],
        decision: str,
        latest_decision: str,
    ) -> None:
        if latest_decision == "reject":
            if decision != "reject":
                raise MemoryReviewError("Candidate already has a terminal owner REJECT decision.")
            return
        if latest_decision == "revoke":
            if decision != "revoke":
                raise MemoryReviewError("Canonical memory was revoked and cannot be re-promoted in V1.")
            return
        if latest_decision == "promote":
            if decision not in {"promote", "revoke"}:
                raise MemoryReviewError("Promoted canonical memory may only be repeated or revoked in V1.")
            return
        if latest_decision == "defer":
            if decision not in {"defer", "promote", "reject"}:
                raise MemoryReviewError("Deferred candidate may only be deferred, promoted, or rejected.")
            return
        if latest_decision == "":
            if decision == "revoke":
                raise MemoryReviewError("Only a promoted canonical memory can be revoked.")
            return
        raise MemoryReviewError("Unsupported prior decision state.")

    def _promotion_checks(self, candidate: dict[str, Any]) -> None:
        # V1 refuses assistant-origin durable promotion entirely. The owner can
        # restate a verified fact in their own message and promote that instead.
        if str(candidate.get("source_role") or "") != "user":
            raise MemoryReviewError(
                "Promotion blocked: assistant-origin candidates cannot become canonical Memory in V1; owner must restate the verified fact."
            )
        if str(candidate.get("trust_tier") or "") != "owner_message_unverified":
            raise MemoryReviewError("Promotion blocked: unsupported candidate trust tier.")
        risks = _canonical_risks(str(candidate.get("content") or ""))
        if "possible_secret" in risks:
            raise MemoryReviewError(
                "Promotion blocked: candidate appears to contain secret material."
            )
        if "instruction_like" in risks:
            raise MemoryReviewError(
                "Promotion blocked: candidate contains instruction-like content unsuitable for canonical Memory."
            )

    def prepare_review(
        self,
        *,
        candidate_id: str,
        decision: str,
        expected_content_sha256: str,
        owner_scope: str = OWNER_SCOPE,
        actor_fingerprint: str,
    ) -> dict[str, Any]:
        decision = _clean(decision, 20).lower()
        if decision not in _ALLOWED:
            raise MemoryReviewError("decision must be promote, reject, defer, or revoke.")
        if _clean(owner_scope, 120) != OWNER_SCOPE:
            raise MemoryReviewError("Unsupported owner_scope.")
        actor_fingerprint = _clean(actor_fingerprint, 120)
        if not actor_fingerprint:
            raise MemoryReviewError("Owner actor fingerprint is required.")

        candidate = self._candidate(candidate_id)
        expected = _clean(expected_content_sha256, 64).lower()
        actual = str(candidate.get("content_sha256") or "").lower()
        if not expected or expected != actual:
            raise MemoryReviewError("Candidate content hash mismatch; refresh review state.")

        latest = self._latest_by_candidate().get(candidate["candidate_id"])
        latest_decision = str(latest["decision"]) if latest else ""
        self._validate_transition(candidate, decision, latest_decision)
        if decision == "promote":
            self._promotion_checks(candidate)

        token = secrets.token_urlsafe(32)
        token_hash = _sha256_text(token)
        now = time.monotonic()
        with self._lock:
            self._purge_expired_tickets_locked(now)
            self._review_tickets[token_hash] = {
                "candidate_id": candidate["candidate_id"],
                "decision": decision,
                "expected_content_sha256": actual,
                "owner_scope": OWNER_SCOPE,
                "actor_fingerprint": actor_fingerprint,
                "expires_monotonic": now + REVIEW_TICKET_TTL_SECONDS,
            }
        return {
            "ok": True,
            "review_token": token,
            "expires_in_seconds": REVIEW_TICKET_TTL_SECONDS,
            "candidate_id": candidate["candidate_id"],
            "decision": decision,
            "content_sha256": actual,
            "authority": "owner_explicit_review_only",
        }

    def _purge_expired_tickets_locked(self, now: float) -> None:
        expired = [
            k
            for k, v in self._review_tickets.items()
            if float(v.get("expires_monotonic") or 0.0) <= now
        ]
        for key in expired:
            self._review_tickets.pop(key, None)

    def _consume_review_ticket(
        self,
        *,
        review_token: str,
        candidate_id: str,
        decision: str,
        expected_content_sha256: str,
        owner_scope: str,
        actor_fingerprint: str,
    ) -> str:
        token = _clean(review_token, 256)
        if not token:
            raise MemoryReviewError("One-time owner review token is required.")
        token_hash = _sha256_text(token)
        now = time.monotonic()
        with self._lock:
            self._purge_expired_tickets_locked(now)
            ticket = self._review_tickets.pop(token_hash, None)
        if not ticket:
            raise MemoryReviewError("Owner review token is invalid, expired, or already used.")

        expected = {
            "candidate_id": _clean(candidate_id, 120),
            "decision": _clean(decision, 20).lower(),
            "expected_content_sha256": _clean(expected_content_sha256, 64).lower(),
            "owner_scope": _clean(owner_scope, 120),
            "actor_fingerprint": _clean(actor_fingerprint, 120),
        }
        for key, value in expected.items():
            if str(ticket.get(key) or "") != value:
                raise MemoryReviewError("Owner review token binding mismatch.")
        return token_hash

    def candidates_view(self) -> dict[str, Any]:
        base = self.candidates.list()
        latest = self._latest_by_candidate()
        all_memories = {
            x["candidate_id"]: x
            for x in self.list_canonical(include_revoked=True).get("all_memories", [])
        }
        out = []
        counts = {"pending": 0, "defer": 0, "promote": 0, "reject": 0, "revoke": 0}
        for item in base.get("candidates", []):
            c = copy.deepcopy(item)
            event = latest.get(str(c.get("candidate_id") or ""))
            if event:
                decision = str(event["decision"])
                c["decision"] = decision
                c["decision_reason"] = event["reason"]
                c["decision_rule_id"] = event["rule_id"]
                c["decided_at"] = int(event["decided_at_ms"])
                c["decision_id"] = event["decision_id"]
                c["decision_event_hash"] = event["event_hash"]
                c["decision_event_index"] = int(event["event_index"])
                c["decision_actor_fingerprint"] = event["actor_fingerprint"]
                c["status"] = {
                    "defer": "deferred",
                    "promote": "promoted",
                    "reject": "rejected",
                    "revoke": "revoked",
                }[decision]
                c["canonical"] = decision == "promote"
                c["authority"] = "canonical_context" if decision == "promote" else "candidate_only"
                if decision in {"promote", "revoke"}:
                    c["durable_memory_id"] = all_memories.get(c["candidate_id"], {}).get(
                        "memory_id", ""
                    )
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
            "promotion_authority": "paired-owner-token + explicit-ui-gesture + one-time-server-review-token",
            "candidates": out,
            "count": len(out),
            "pending_count": counts.get("pending", 0),
            "deferred_count": counts.get("defer", 0),
            "promoted_count": counts.get("promote", 0),
            "rejected_count": counts.get("reject", 0),
            "revoked_count": counts.get("revoke", 0),
            "canonical_memory_written": bool(
                counts.get("promote", 0) or counts.get("revoke", 0)
            ),
        }

    def decide(
        self,
        *,
        candidate_id: str,
        decision: str,
        expected_content_sha256: str,
        review_token: str,
        owner_scope: str = OWNER_SCOPE,
        actor_fingerprint: str,
    ) -> dict[str, Any]:
        decision = _clean(decision, 20).lower()
        if decision not in _ALLOWED:
            raise MemoryReviewError("decision must be promote, reject, defer, or revoke.")
        if _clean(owner_scope, 120) != OWNER_SCOPE:
            raise MemoryReviewError("Unsupported owner_scope.")
        actor_fingerprint = _clean(actor_fingerprint, 120)
        if not actor_fingerprint:
            raise MemoryReviewError("Owner actor fingerprint is required.")

        candidate = self._candidate(candidate_id)
        expected = _clean(expected_content_sha256, 64).lower()
        actual = str(candidate.get("content_sha256") or "").lower()
        if not expected or expected != actual:
            raise MemoryReviewError("Candidate content hash mismatch; refresh review state.")

        ticket_hash = self._consume_review_ticket(
            review_token=review_token,
            candidate_id=candidate["candidate_id"],
            decision=decision,
            expected_content_sha256=actual,
            owner_scope=OWNER_SCOPE,
            actor_fingerprint=actor_fingerprint,
        )

        if decision == "promote":
            self._promotion_checks(candidate)

        now_ms = int(time.time() * 1000)
        reason = "owner_explicit_review"
        snapshot_json = _canonical_json(candidate)

        with self._lock, closing(self._connect()) as con:
            con.execute("BEGIN IMMEDIATE")
            try:
                latest = con.execute(
                    "SELECT * FROM decision_events WHERE candidate_id=? "
                    "ORDER BY event_index DESC LIMIT 1",
                    (candidate["candidate_id"],),
                ).fetchone()
                latest_decision = str(latest["decision"]) if latest is not None else ""
                self._validate_transition(candidate, decision, latest_decision)

                if latest is not None:
                    latest_dict = dict(latest)
                    if latest_decision == decision and decision in {"promote", "reject", "defer", "revoke"}:
                        con.rollback()
                        return self._decision_result(
                            candidate,
                            latest_dict,
                            created=False,
                            memory=self._memory_for_candidate(
                                candidate["candidate_id"],
                                active=(latest_decision == "promote"),
                            ),
                        )

                previous = con.execute(
                    "SELECT event_index,event_hash FROM decision_events "
                    "ORDER BY event_index DESC LIMIT 1"
                ).fetchone()
                prev_hash = str(previous["event_hash"]) if previous else ""
                event_index = int(previous["event_index"]) + 1 if previous else 1

                event_payload = {
                    "schema": DECISION_SCHEMA,
                    "event_index": event_index,
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
                    "actor_fingerprint": actor_fingerprint,
                    "review_ticket_sha256": ticket_hash,
                    "candidate_snapshot_sha256": _sha256_text(snapshot_json),
                    "decided_at_ms": now_ms,
                    "prev_event_hash": prev_hash,
                }
                event_hash = _sha256_text(_canonical_json(event_payload))
                decision_id = "md_" + event_hash[:24]

                con.execute(
                    """
                    INSERT INTO decision_events(
                        event_index,decision_id,schema,candidate_id,candidate_content_sha256,
                        decision,rule_id,reason,owner_scope,project_id,source_ref,
                        trust_origin,trust_tier,actor_fingerprint,review_ticket_sha256,
                        candidate_snapshot_json,decided_at_ms,prev_event_hash,event_hash
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        event_index,
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
                        actor_fingerprint,
                        ticket_hash,
                        snapshot_json,
                        now_ms,
                        prev_hash,
                        event_hash,
                    ),
                )

                memory = self._memory_for_candidate(candidate["candidate_id"], active=True)
                if decision == "promote" and memory is None:
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
                        ).fetchone(),
                        active=True,
                    )
                elif decision in {"reject", "defer", "revoke"}:
                    memory = None

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
                    SELECT candidate_id, MAX(event_index) AS max_event_index
                    FROM decision_events
                    GROUP BY candidate_id
                ) latest
                  ON latest.candidate_id=d.candidate_id
                 AND latest.max_event_index=d.event_index
                """
            ).fetchall()
        return {str(row["candidate_id"]): dict(row) for row in rows}

    def _memory_for_candidate(
        self,
        candidate_id: str,
        *,
        active: bool,
    ) -> dict[str, Any] | None:
        with self._lock, closing(self._connect()) as con:
            row = con.execute(
                "SELECT * FROM canonical_memories WHERE candidate_id=?",
                (candidate_id,),
            ).fetchone()
            return self._memory_public(row, active=active) if row is not None else None

    def list_canonical(self, *, include_revoked: bool = False) -> dict[str, Any]:
        latest = self._latest_by_candidate()
        with self._lock, closing(self._connect()) as con:
            rows = con.execute(
                "SELECT * FROM canonical_memories ORDER BY created_at_ms DESC, memory_id DESC"
            ).fetchall()

        active_memories: list[dict[str, Any]] = []
        revoked_memories: list[dict[str, Any]] = []
        all_memories: list[dict[str, Any]] = []
        for row in rows:
            candidate_id = str(row["candidate_id"])
            decision = str(latest.get(candidate_id, {}).get("decision") or "promote")
            active = decision == "promote"
            memory = self._memory_public(row, active=active)
            all_memories.append(memory)
            if active:
                active_memories.append(memory)
            else:
                revoked_memories.append(memory)

        result = {
            "schema": "orion.canonical-memory-list/1",
            "owner_scope": OWNER_SCOPE,
            "authority": "context_only",
            "memories": active_memories,
            "count": len(active_memories),
            "revoked_count": len(revoked_memories),
            "tamper_evidence_scope": (
                "hash chain detects in-database event mutation/reordering; "
                "wholesale local DB replacement requires future external anchoring"
            ),
        }
        if include_revoked:
            result["revoked_memories"] = revoked_memories
            result["all_memories"] = all_memories
        return result

    def decisions(self) -> dict[str, Any]:
        with self._lock, closing(self._connect()) as con:
            rows = con.execute(
                "SELECT * FROM decision_events ORDER BY event_index ASC"
            ).fetchall()
            events = [self._decision_public(dict(row)) for row in rows]
        return {
            "schema": "orion.memory-decision-log/1",
            "append_only": True,
            "tamper_evidence_scope": (
                "in-database hash chain only; wholesale DB replacement is not "
                "detectable until a future external anchor is added"
            ),
            "events": events,
            "count": len(events),
        }

    def audit_chain(self) -> dict[str, Any]:
        with self._lock, closing(self._connect()) as con:
            rows = con.execute(
                "SELECT * FROM decision_events ORDER BY event_index ASC"
            ).fetchall()

        prev = ""
        problems: list[str] = []
        expected_index = 1
        for row in rows:
            r = dict(row)
            if int(r["event_index"]) != expected_index:
                problems.append(
                    f"event_index {r['event_index']}: expected {expected_index}"
                )
            if r["prev_event_hash"] != prev:
                problems.append(f"event_index {r['event_index']}: prev hash mismatch")
            snapshot_sha = _sha256_text(r["candidate_snapshot_json"])
            payload = {
                "schema": r["schema"],
                "event_index": int(r["event_index"]),
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
                "actor_fingerprint": r["actor_fingerprint"],
                "review_ticket_sha256": r["review_ticket_sha256"],
                "candidate_snapshot_sha256": snapshot_sha,
                "decided_at_ms": int(r["decided_at_ms"]),
                "prev_event_hash": r["prev_event_hash"],
            }
            expected = _sha256_text(_canonical_json(payload))
            if expected != r["event_hash"]:
                problems.append(
                    f"event_index {r['event_index']}: event hash mismatch"
                )
            prev = r["event_hash"]
            expected_index += 1

        return {
            "schema": "orion.memory-decision-audit/1",
            "ok": not problems,
            "events": len(rows),
            "head_hash": prev,
            "problems": problems,
            "tamper_evidence_scope": (
                "in-database chain only; wholesale local DB replacement is not detectable"
            ),
        }

    @staticmethod
    def _decision_public(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "event_index": int(row["event_index"]),
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
            "actor_fingerprint": row["actor_fingerprint"],
            "decided_at_ms": int(row["decided_at_ms"]),
            "prev_event_hash": row["prev_event_hash"],
            "event_hash": row["event_hash"],
        }

    @staticmethod
    def _memory_public(
        row: sqlite3.Row | dict[str, Any],
        *,
        active: bool,
    ) -> dict[str, Any]:
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
            "status": "active" if active else "revoked",
            "active": bool(active),
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
            "canonical_memory_written": (
                str(event.get("decision") or "") == "promote" and memory is not None
            ),
            "canonical_memory_revoked": str(event.get("decision") or "") == "revoke",
            "memory": memory,
        }
