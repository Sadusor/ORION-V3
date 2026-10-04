from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping
from uuid import uuid4


class StateStoreError(RuntimeError):
    pass


class EventType(str, Enum):
    PROPOSAL = "PROPOSAL"
    REVIEW = "REVIEW"
    DECISION = "DECISION"
    ACTION = "ACTION"
    EVIDENCE = "EVIDENCE"
    RESULT = "RESULT"
    FAILURE = "FAILURE"
    MEMORY_PROMOTED = "MEMORY_PROMOTED"
    MEMORY_SUPERSEDED = "MEMORY_SUPERSEDED"


class MemoryKind(str, Enum):
    PROJECT_FACT = "PROJECT_FACT"
    DECISION = "DECISION"
    CURRENT_STATE = "CURRENT_STATE"
    FAILURE_LESSON = "FAILURE_LESSON"
    CAPABILITY = "CAPABILITY"
    EVIDENCE_REF = "EVIDENCE_REF"
    USER_PREFERENCE = "USER_PREFERENCE"


class MemoryStatus(str, Enum):
    CURRENT = "CURRENT"
    SUPERSEDED = "SUPERSEDED"
    RETRACTED = "RETRACTED"


@dataclass(frozen=True)
class ProjectRecord:
    project_id: str
    name: str
    created_at: str
    metadata: Mapping[str, Any]


@dataclass(frozen=True)
class TaskRecord:
    task_id: str
    project_id: str
    objective: str
    status: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class EventRecord:
    event_id: str
    project_id: str
    task_id: str | None
    attempt_id: str | None
    event_type: EventType
    actor_kind: str
    actor_id: str
    created_at: str
    payload: Mapping[str, Any]
    payload_sha256: str
    parent_event_id: str | None


@dataclass(frozen=True)
class MemoryRecord:
    memory_id: str
    project_id: str
    kind: MemoryKind
    memory_key: str
    summary: str
    value: Any
    source_event_id: str
    promoted_by: str
    created_at: str
    supersedes_memory_id: str | None
    status: MemoryStatus


_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    objective TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tasks_project_updated
    ON tasks(project_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    task_id TEXT REFERENCES tasks(task_id),
    attempt_id TEXT,
    event_type TEXT NOT NULL,
    actor_kind TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    parent_event_id TEXT REFERENCES events(event_id)
);
CREATE INDEX IF NOT EXISTS idx_events_project_created
    ON events(project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_task_created
    ON events(task_id, created_at DESC);

CREATE TRIGGER IF NOT EXISTS events_no_update
BEFORE UPDATE ON events
BEGIN
    SELECT RAISE(ABORT, 'ORION events are append-only');
END;

CREATE TRIGGER IF NOT EXISTS events_no_delete
BEFORE DELETE ON events
BEGIN
    SELECT RAISE(ABORT, 'ORION events are append-only');
END;

CREATE TABLE IF NOT EXISTS exchange_receipts (
    event_id TEXT NOT NULL REFERENCES events(event_id),
    recipient TEXT NOT NULL,
    acknowledged_at TEXT NOT NULL,
    PRIMARY KEY(event_id, recipient)
);

CREATE TRIGGER IF NOT EXISTS exchange_receipts_no_update
BEFORE UPDATE ON exchange_receipts
BEGIN
    SELECT RAISE(ABORT, 'ORION exchange receipts are append-only');
END;

CREATE TRIGGER IF NOT EXISTS exchange_receipts_no_delete
BEFORE DELETE ON exchange_receipts
BEGIN
    SELECT RAISE(ABORT, 'ORION exchange receipts are append-only');
END;

CREATE TABLE IF NOT EXISTS memories (
    memory_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    kind TEXT NOT NULL,
    memory_key TEXT NOT NULL,
    summary TEXT NOT NULL,
    value_json TEXT NOT NULL,
    source_event_id TEXT NOT NULL REFERENCES events(event_id),
    promoted_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    supersedes_memory_id TEXT REFERENCES memories(memory_id),
    status TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_memories_project_kind
    ON memories(project_id, kind, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_memories_one_current_key
    ON memories(project_id, kind, memory_key)
    WHERE status = 'CURRENT';
"""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _payload_hash(payload: Mapping[str, Any]) -> tuple[str, str]:
    encoded = _canonical_json(dict(payload))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return encoded, digest


class OrionStateStore:
    """Small authoritative SQLite store for ORION state, events and Memory."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    def initialize(self) -> None:
        self.connect().executescript(_SCHEMA)
        self.connect().commit()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def create_project(
        self,
        name: str,
        *,
        project_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> ProjectRecord:
        name = name.strip()
        if not name:
            raise StateStoreError("project name must be non-empty")
        record = ProjectRecord(
            project_id=project_id or str(uuid4()),
            name=name,
            created_at=_utc_now(),
            metadata=dict(metadata or {}),
        )
        self.connect().execute(
            "INSERT INTO projects(project_id,name,created_at,metadata_json) VALUES(?,?,?,?)",
            (
                record.project_id,
                record.name,
                record.created_at,
                _canonical_json(record.metadata),
            ),
        )
        self.connect().commit()
        return record

    def get_project(self, project_id: str) -> ProjectRecord | None:
        row = self.connect().execute(
            "SELECT * FROM projects WHERE project_id=?",
            (project_id,),
        ).fetchone()
        if row is None:
            return None
        return ProjectRecord(
            project_id=row["project_id"],
            name=row["name"],
            created_at=row["created_at"],
            metadata=json.loads(row["metadata_json"]),
        )

    def get_task(self, task_id: str) -> TaskRecord | None:
        return self._get_task(task_id)

    def list_task_events(
        self,
        project_id: str,
        task_id: str,
        *,
        limit: int = 50,
    ) -> list[EventRecord]:
        self._require_project(project_id)
        task = self._get_task(task_id)
        if task is None or task.project_id != project_id:
            raise StateStoreError("task does not belong to project")
        if limit < 1 or limit > 100:
            raise StateStoreError("event limit must be between 1 and 100")
        rows = self.connect().execute(
            """
            SELECT * FROM (
                SELECT rowid AS _seq, * FROM events
                WHERE project_id=? AND task_id=?
                ORDER BY rowid DESC
                LIMIT ?
            )
            ORDER BY _seq ASC
            """,
            (project_id, task_id, limit),
        ).fetchall()
        return [self._row_to_event(row) for row in rows]

    def create_task(
        self,
        project_id: str,
        objective: str,
        *,
        task_id: str | None = None,
        status: str = "queued",
    ) -> TaskRecord:
        self._require_project(project_id)
        objective = objective.strip()
        if not objective:
            raise StateStoreError("task objective must be non-empty")
        now = _utc_now()
        record = TaskRecord(
            task_id=task_id or str(uuid4()),
            project_id=project_id,
            objective=objective,
            status=status,
            created_at=now,
            updated_at=now,
        )
        self.connect().execute(
            """
            INSERT INTO tasks(task_id,project_id,objective,status,created_at,updated_at)
            VALUES(?,?,?,?,?,?)
            """,
            (
                record.task_id,
                record.project_id,
                record.objective,
                record.status,
                record.created_at,
                record.updated_at,
            ),
        )
        self.connect().commit()
        return record

    def append_event(
        self,
        project_id: str,
        event_type: EventType,
        payload: Mapping[str, Any],
        *,
        actor_kind: str,
        actor_id: str,
        task_id: str | None = None,
        attempt_id: str | None = None,
        parent_event_id: str | None = None,
        event_id: str | None = None,
        commit: bool = True,
    ) -> EventRecord:
        self._require_project(project_id)
        if task_id is not None:
            task = self._get_task(task_id)
            if task is None or task.project_id != project_id:
                raise StateStoreError("task does not belong to project")
        if parent_event_id is not None:
            parent = self.get_event(parent_event_id)
            if parent is None:
                raise StateStoreError("parent event does not exist")
            if parent.project_id != project_id:
                raise StateStoreError("parent event belongs to another project")
            if (
                task_id is not None
                and parent.task_id is not None
                and parent.task_id != task_id
            ):
                raise StateStoreError("parent event belongs to another task")

        actor_kind = actor_kind.strip()
        actor_id = actor_id.strip()
        if not actor_kind or not actor_id:
            raise StateStoreError("actor kind/id must be non-empty")

        payload_json, payload_sha256 = _payload_hash(payload)
        record = EventRecord(
            event_id=event_id or str(uuid4()),
            project_id=project_id,
            task_id=task_id,
            attempt_id=attempt_id,
            event_type=event_type,
            actor_kind=actor_kind,
            actor_id=actor_id,
            created_at=_utc_now(),
            payload=dict(payload),
            payload_sha256=payload_sha256,
            parent_event_id=parent_event_id,
        )
        self.connect().execute(
            """
            INSERT INTO events(
                event_id,project_id,task_id,attempt_id,event_type,actor_kind,
                actor_id,created_at,payload_json,payload_sha256,parent_event_id
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                record.event_id,
                record.project_id,
                record.task_id,
                record.attempt_id,
                record.event_type.value,
                record.actor_kind,
                record.actor_id,
                record.created_at,
                payload_json,
                record.payload_sha256,
                record.parent_event_id,
            ),
        )
        if commit:
            self.connect().commit()
        return record

    def get_event(self, event_id: str) -> EventRecord | None:
        row = self.connect().execute(
            "SELECT * FROM events WHERE event_id=?",
            (event_id,),
        ).fetchone()
        return self._row_to_event(row) if row else None

    def promote_memory(
        self,
        project_id: str,
        kind: MemoryKind,
        memory_key: str,
        summary: str,
        value: Any,
        *,
        source_event_id: str,
        promoted_by: str,
        supersedes_memory_id: str | None = None,
        memory_id: str | None = None,
    ) -> MemoryRecord:
        self._require_project(project_id)
        source = self.get_event(source_event_id)
        if source is None:
            raise StateStoreError("source event does not exist")
        if source.project_id != project_id:
            raise StateStoreError("source event belongs to another project")

        memory_key = memory_key.strip()
        summary = summary.strip()
        promoted_by = promoted_by.strip()
        if not memory_key or not summary or not promoted_by:
            raise StateStoreError("memory key/summary/promoted_by must be non-empty")

        current = self._current_memory(project_id, kind, memory_key)
        if current is not None and supersedes_memory_id is None:
            raise StateStoreError(
                "current memory exists; explicit supersession is required"
            )
        if supersedes_memory_id is not None:
            if current is None:
                raise StateStoreError("no current memory exists to supersede")
            if current.memory_id != supersedes_memory_id:
                raise StateStoreError("supersedes_memory_id is not the current record")
        elif current is None:
            supersedes_memory_id = None

        now = _utc_now()
        record = MemoryRecord(
            memory_id=memory_id or str(uuid4()),
            project_id=project_id,
            kind=kind,
            memory_key=memory_key,
            summary=summary,
            value=value,
            source_event_id=source_event_id,
            promoted_by=promoted_by,
            created_at=now,
            supersedes_memory_id=supersedes_memory_id,
            status=MemoryStatus.CURRENT,
        )

        conn = self.connect()
        try:
            conn.execute("BEGIN")
            if current is not None:
                conn.execute(
                    "UPDATE memories SET status=? WHERE memory_id=? AND status=?",
                    (
                        MemoryStatus.SUPERSEDED.value,
                        current.memory_id,
                        MemoryStatus.CURRENT.value,
                    ),
                )
            conn.execute(
                """
                INSERT INTO memories(
                    memory_id,project_id,kind,memory_key,summary,value_json,
                    source_event_id,promoted_by,created_at,supersedes_memory_id,status
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    record.memory_id,
                    record.project_id,
                    record.kind.value,
                    record.memory_key,
                    record.summary,
                    _canonical_json(record.value),
                    record.source_event_id,
                    record.promoted_by,
                    record.created_at,
                    record.supersedes_memory_id,
                    record.status.value,
                ),
            )
            audit_type = (
                EventType.MEMORY_SUPERSEDED
                if current is not None
                else EventType.MEMORY_PROMOTED
            )
            audit_payload = {
                "memory_id": record.memory_id,
                "kind": record.kind.value,
                "memory_key": record.memory_key,
                "source_event_id": record.source_event_id,
                "supersedes_memory_id": record.supersedes_memory_id,
            }
            self._insert_event_in_transaction(
                project_id,
                audit_type,
                audit_payload,
                actor_kind="memory_gate",
                actor_id=promoted_by,
                parent_event_id=source_event_id,
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        return record

    def get_memory(self, memory_id: str) -> MemoryRecord | None:
        row = self.connect().execute(
            "SELECT * FROM memories WHERE memory_id=?",
            (memory_id,),
        ).fetchone()
        return self._row_to_memory(row) if row else None

    def get_l1(
        self,
        project_id: str,
        *,
        kinds: Iterable[MemoryKind] | None = None,
        limit: int = 20,
    ) -> list[MemoryRecord]:
        self._require_project(project_id)
        if limit < 1 or limit > 100:
            raise StateStoreError("L1 limit must be between 1 and 100")
        params: list[Any] = [project_id, MemoryStatus.CURRENT.value]
        where = "project_id=? AND status=?"
        kind_values = [kind.value for kind in kinds] if kinds is not None else []
        if kind_values:
            placeholders = ",".join("?" for _ in kind_values)
            where += f" AND kind IN ({placeholders})"
            params.extend(kind_values)
        params.append(limit)
        rows = self.connect().execute(
            f"""
            SELECT * FROM memories
            WHERE {where}
            ORDER BY created_at DESC, memory_id
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [self._row_to_memory(row) for row in rows]

    def get_l0(self, project_id: str) -> dict[str, Any]:
        project = self._require_project(project_id)
        task_rows = self.connect().execute(
            """
            SELECT * FROM tasks WHERE project_id=?
            ORDER BY updated_at DESC, task_id LIMIT 3
            """,
            (project_id,),
        ).fetchall()
        state = self.get_l1(
            project_id,
            kinds=[MemoryKind.CURRENT_STATE],
            limit=5,
        )
        decisions = self.get_l1(
            project_id,
            kinds=[MemoryKind.DECISION],
            limit=5,
        )
        event_rows = self.connect().execute(
            """
            SELECT * FROM events
            WHERE project_id=? AND event_type IN (?,?)
            ORDER BY created_at DESC, event_id LIMIT 5
            """,
            (
                project_id,
                EventType.RESULT.value,
                EventType.FAILURE.value,
            ),
        ).fetchall()
        return {
            "project": {
                "project_id": project.project_id,
                "name": project.name,
            },
            "tasks": [
                {
                    "task_id": row["task_id"],
                    "objective": row["objective"],
                    "status": row["status"],
                    "updated_at": row["updated_at"],
                }
                for row in task_rows
            ],
            "current_state": [
                {
                    "memory_id": item.memory_id,
                    "key": item.memory_key,
                    "summary": item.summary,
                }
                for item in state
            ],
            "decisions": [
                {
                    "memory_id": item.memory_id,
                    "key": item.memory_key,
                    "summary": item.summary,
                }
                for item in decisions
            ],
            "recent_outcomes": [
                {
                    "event_id": row["event_id"],
                    "event_type": row["event_type"],
                    "payload_sha256": row["payload_sha256"],
                }
                for row in event_rows
            ],
        }

    def get_l2(self, project_id: str, memory_id: str) -> dict[str, Any]:
        self._require_project(project_id)
        memory = self.get_memory(memory_id)
        if memory is None or memory.project_id != project_id:
            raise StateStoreError("memory does not belong to project")
        source = self.get_event(memory.source_event_id)
        if source is None or source.project_id != project_id:
            raise StateStoreError("memory source event is unavailable")
        parent = (
            self.get_event(source.parent_event_id)
            if source.parent_event_id is not None
            else None
        )
        return {
            "memory": memory,
            "source_event": source,
            "parent_event": parent,
        }

    def _insert_event_in_transaction(
        self,
        project_id: str,
        event_type: EventType,
        payload: Mapping[str, Any],
        *,
        actor_kind: str,
        actor_id: str,
        parent_event_id: str | None,
    ) -> None:
        payload_json, digest = _payload_hash(payload)
        self.connect().execute(
            """
            INSERT INTO events(
                event_id,project_id,task_id,attempt_id,event_type,actor_kind,
                actor_id,created_at,payload_json,payload_sha256,parent_event_id
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                str(uuid4()),
                project_id,
                None,
                None,
                event_type.value,
                actor_kind,
                actor_id,
                _utc_now(),
                payload_json,
                digest,
                parent_event_id,
            ),
        )

    def _current_memory(
        self,
        project_id: str,
        kind: MemoryKind,
        memory_key: str,
    ) -> MemoryRecord | None:
        row = self.connect().execute(
            """
            SELECT * FROM memories
            WHERE project_id=? AND kind=? AND memory_key=? AND status=?
            """,
            (
                project_id,
                kind.value,
                memory_key,
                MemoryStatus.CURRENT.value,
            ),
        ).fetchone()
        return self._row_to_memory(row) if row else None

    def _require_project(self, project_id: str) -> ProjectRecord:
        project = self.get_project(project_id)
        if project is None:
            raise StateStoreError("project does not exist")
        return project

    def _get_task(self, task_id: str) -> TaskRecord | None:
        row = self.connect().execute(
            "SELECT * FROM tasks WHERE task_id=?",
            (task_id,),
        ).fetchone()
        if row is None:
            return None
        return TaskRecord(
            task_id=row["task_id"],
            project_id=row["project_id"],
            objective=row["objective"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> EventRecord:
        return EventRecord(
            event_id=row["event_id"],
            project_id=row["project_id"],
            task_id=row["task_id"],
            attempt_id=row["attempt_id"],
            event_type=EventType(row["event_type"]),
            actor_kind=row["actor_kind"],
            actor_id=row["actor_id"],
            created_at=row["created_at"],
            payload=json.loads(row["payload_json"]),
            payload_sha256=row["payload_sha256"],
            parent_event_id=row["parent_event_id"],
        )

    @staticmethod
    def _row_to_memory(row: sqlite3.Row) -> MemoryRecord:
        return MemoryRecord(
            memory_id=row["memory_id"],
            project_id=row["project_id"],
            kind=MemoryKind(row["kind"]),
            memory_key=row["memory_key"],
            summary=row["summary"],
            value=json.loads(row["value_json"]),
            source_event_id=row["source_event_id"],
            promoted_by=row["promoted_by"],
            created_at=row["created_at"],
            supersedes_memory_id=row["supersedes_memory_id"],
            status=MemoryStatus(row["status"]),
        )


__all__ = [
    "EventRecord",
    "EventType",
    "MemoryKind",
    "MemoryRecord",
    "MemoryStatus",
    "OrionStateStore",
    "ProjectRecord",
    "StateStoreError",
    "TaskRecord",
]
