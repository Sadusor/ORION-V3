from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from secrets import token_urlsafe
from time import time
from typing import Any, Callable, Mapping
from uuid import uuid4

from .store import OrionStateStore, StateStoreError


class AttemptDenied(StateStoreError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class AttemptRecord:
    attempt_id: str
    project_id: str
    task_id: str
    status: str
    lease_generation: int
    lease_worker_id: str | None
    lease_issued_at: float | None
    lease_expires_at: float | None
    lease_revoked_at: float | None
    checkpoint_seq: int
    checkpoint: Any
    result: Any
    stopped_at: float | None
    stop_reason: str | None
    created_at: float
    updated_at: float


@dataclass(frozen=True)
class AttemptLease:
    attempt_id: str
    project_id: str
    task_id: str
    worker_id: str
    generation: int
    issued_at: float
    expires_at: float


@dataclass(frozen=True)
class IssuedAttemptLease:
    token: str
    lease: AttemptLease


_ATTEMPT_SCHEMA = """
CREATE TABLE IF NOT EXISTS attempts (
    attempt_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    task_id TEXT NOT NULL REFERENCES tasks(task_id),
    status TEXT NOT NULL,
    lease_generation INTEGER NOT NULL DEFAULT 0,
    lease_token_hash TEXT,
    lease_worker_id TEXT,
    lease_issued_at REAL,
    lease_expires_at REAL,
    lease_revoked_at REAL,
    checkpoint_seq INTEGER NOT NULL DEFAULT 0,
    checkpoint_json TEXT,
    result_json TEXT,
    stopped_at REAL,
    stop_reason TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_attempts_task_created
    ON attempts(task_id, created_at DESC);
"""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class AttemptAuthority:
    """Durable ORION-owned Attempt ownership with fenced short-lived leases."""

    TERMINAL = frozenset({"SUCCEEDED", "FAILED"})

    def __init__(
        self,
        store: OrionStateStore,
        *,
        clock: Callable[[], float] = time,
        token_factory: Callable[[], str] | None = None,
    ) -> None:
        self._store = store
        self._clock = clock
        self._token_factory = token_factory or (lambda: token_urlsafe(32))

    def initialize(self) -> None:
        self._store.connect().executescript(_ATTEMPT_SCHEMA)
        self._store.connect().commit()

    @staticmethod
    def _hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def create_attempt(
        self,
        task_id: str,
        *,
        attempt_id: str | None = None,
    ) -> AttemptRecord:
        task = self._store.get_task(task_id)
        if task is None:
            raise AttemptDenied("unknown_task", "Task does not exist.")
        now = float(self._clock())
        attempt_id = attempt_id or str(uuid4())
        self._store.connect().execute(
            """
            INSERT INTO attempts(
                attempt_id,project_id,task_id,status,created_at,updated_at
            ) VALUES(?,?,?,?,?,?)
            """,
            (attempt_id, task.project_id, task.task_id, "PENDING", now, now),
        )
        self._store.connect().commit()
        return self.get_attempt(attempt_id)

    def get_attempt(self, attempt_id: str) -> AttemptRecord:
        row = self._store.connect().execute(
            "SELECT * FROM attempts WHERE attempt_id=?",
            (attempt_id,),
        ).fetchone()
        if row is None:
            raise AttemptDenied("unknown_attempt", "Attempt does not exist.")
        return self._row_to_attempt(row)

    def claim(
        self,
        attempt_id: str,
        *,
        worker_id: str,
        ttl_seconds: float,
    ) -> IssuedAttemptLease:
        worker_id = worker_id.strip()
        if not worker_id:
            raise ValueError("worker_id must be non-empty")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")

        raw_token = self._token_factory()
        if not raw_token:
            raise ValueError("token factory returned an empty token")
        now = float(self._clock())
        conn = self._store.connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM attempts WHERE attempt_id=?",
                (attempt_id,),
            ).fetchone()
            if row is None:
                raise AttemptDenied("unknown_attempt", "Attempt does not exist.")
            self._ensure_claimable(row, now)
            generation = int(row["lease_generation"]) + 1
            token = f"{generation}.{raw_token}"
            token_hash = self._hash(token)
            expires_at = now + float(ttl_seconds)
            conn.execute(
                """
                UPDATE attempts
                SET status='RUNNING',
                    lease_generation=?,
                    lease_token_hash=?,
                    lease_worker_id=?,
                    lease_issued_at=?,
                    lease_expires_at=?,
                    lease_revoked_at=NULL,
                    updated_at=?
                WHERE attempt_id=?
                """,
                (
                    generation,
                    token_hash,
                    worker_id,
                    now,
                    expires_at,
                    now,
                    attempt_id,
                ),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise

        attempt = self.get_attempt(attempt_id)
        lease = AttemptLease(
            attempt_id=attempt.attempt_id,
            project_id=attempt.project_id,
            task_id=attempt.task_id,
            worker_id=worker_id,
            generation=generation,
            issued_at=now,
            expires_at=expires_at,
        )
        return IssuedAttemptLease(token=token, lease=lease)

    def checkpoint(
        self,
        attempt_id: str,
        token: str | None,
        checkpoint: Mapping[str, Any],
    ) -> AttemptRecord:
        now = float(self._clock())
        conn = self._store.connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = self._validated_row(conn, attempt_id, token, now)
            next_seq = int(row["checkpoint_seq"]) + 1
            conn.execute(
                """
                UPDATE attempts
                SET checkpoint_seq=?, checkpoint_json=?, updated_at=?
                WHERE attempt_id=?
                """,
                (next_seq, _canonical_json(dict(checkpoint)), now, attempt_id),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        return self.get_attempt(attempt_id)

    def finish(
        self,
        attempt_id: str,
        token: str | None,
        *,
        status: str,
        result: Mapping[str, Any],
    ) -> AttemptRecord:
        status = status.upper().strip()
        if status not in self.TERMINAL:
            raise ValueError("status must be SUCCEEDED or FAILED")
        now = float(self._clock())
        conn = self._store.connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            self._validated_row(conn, attempt_id, token, now)
            conn.execute(
                """
                UPDATE attempts
                SET status=?, result_json=?, lease_revoked_at=?, updated_at=?
                WHERE attempt_id=?
                """,
                (status, _canonical_json(dict(result)), now, now, attempt_id),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        return self.get_attempt(attempt_id)

    def stop(
        self,
        attempt_id: str,
        *,
        requested_by: str,
        reason: str,
    ) -> AttemptRecord:
        requested_by = requested_by.strip()
        reason = reason.strip()
        if not requested_by:
            raise ValueError("requested_by must be non-empty")
        if not reason:
            raise ValueError("reason must be non-empty")
        now = float(self._clock())
        conn = self._store.connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM attempts WHERE attempt_id=?",
                (attempt_id,),
            ).fetchone()
            if row is None:
                raise AttemptDenied("unknown_attempt", "Attempt does not exist.")
            if row["status"] in self.TERMINAL:
                raise AttemptDenied("terminal_attempt", "Terminal Attempt cannot be stopped.")
            if row["status"] != "STOPPED":
                conn.execute(
                    """
                    UPDATE attempts
                    SET status='STOPPED',
                        lease_revoked_at=?,
                        stopped_at=?,
                        stop_reason=?,
                        updated_at=?
                    WHERE attempt_id=?
                    """,
                    (now, now, f"{requested_by}: {reason}", now, attempt_id),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        return self.get_attempt(attempt_id)

    def _ensure_claimable(self, row: sqlite3.Row, now: float) -> None:
        status = str(row["status"])
        if status == "STOPPED":
            raise AttemptDenied("stopped_attempt", "Stopped Attempt cannot be claimed.")
        if status in self.TERMINAL:
            raise AttemptDenied("terminal_attempt", "Terminal Attempt cannot be claimed.")

        token_hash = row["lease_token_hash"]
        revoked_at = row["lease_revoked_at"]
        expires_at = row["lease_expires_at"]
        if (
            token_hash is not None
            and revoked_at is None
            and expires_at is not None
            and now < float(expires_at)
        ):
            raise AttemptDenied(
                "active_attempt_lease",
                "Attempt already has an active execution lease.",
            )

    def _validated_row(
        self,
        conn: sqlite3.Connection,
        attempt_id: str,
        token: str | None,
        now: float,
    ) -> sqlite3.Row:
        row = conn.execute(
            "SELECT * FROM attempts WHERE attempt_id=?",
            (attempt_id,),
        ).fetchone()
        if row is None:
            raise AttemptDenied("unknown_attempt", "Attempt does not exist.")
        if row["status"] == "STOPPED":
            raise AttemptDenied("stopped_attempt", "Attempt was stopped.")
        if row["status"] in self.TERMINAL:
            raise AttemptDenied("terminal_attempt", "Attempt is already terminal.")
        if not token:
            raise AttemptDenied("missing_attempt_lease", "Attempt lease is required.")
        expected = row["lease_token_hash"]
        if expected is None or self._hash(token) != expected:
            raise AttemptDenied("stale_attempt_lease", "Attempt lease is not current.")
        if row["lease_revoked_at"] is not None:
            raise AttemptDenied("revoked_attempt_lease", "Attempt lease was revoked.")
        expires_at = row["lease_expires_at"]
        if expires_at is None or now >= float(expires_at):
            raise AttemptDenied("expired_attempt_lease", "Attempt lease expired.")
        return row

    @staticmethod
    def _row_to_attempt(row: sqlite3.Row) -> AttemptRecord:
        return AttemptRecord(
            attempt_id=row["attempt_id"],
            project_id=row["project_id"],
            task_id=row["task_id"],
            status=row["status"],
            lease_generation=int(row["lease_generation"]),
            lease_worker_id=row["lease_worker_id"],
            lease_issued_at=row["lease_issued_at"],
            lease_expires_at=row["lease_expires_at"],
            lease_revoked_at=row["lease_revoked_at"],
            checkpoint_seq=int(row["checkpoint_seq"]),
            checkpoint=json.loads(row["checkpoint_json"]) if row["checkpoint_json"] else None,
            result=json.loads(row["result_json"]) if row["result_json"] else None,
            stopped_at=row["stopped_at"],
            stop_reason=row["stop_reason"],
            created_at=float(row["created_at"]),
            updated_at=float(row["updated_at"]),
        )


__all__ = [
    "AttemptAuthority",
    "AttemptDenied",
    "AttemptLease",
    "AttemptRecord",
    "IssuedAttemptLease",
]
