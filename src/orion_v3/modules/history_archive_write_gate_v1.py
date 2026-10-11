"""Shared SQLite writer gate for staged archive sync and owner deletion.

Disabled integration primitive. Independent processes using the SAME gate DB
must wrap BOTH deletion and sync via run_exclusive; no live route is changed.
SQLite BEGIN IMMEDIATE serializes cooperating writers even across processes.
"""
from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path


class ArchiveWriteGateV1:
    def __init__(self, path: str | Path, *, timeout_seconds: float = 15):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.timeout_seconds = timeout_seconds
        with closing(sqlite3.connect(str(self.path), timeout=timeout_seconds)) as db:
            db.execute("CREATE TABLE IF NOT EXISTS gate_lock (id INTEGER PRIMARY KEY CHECK(id=1), touched INTEGER NOT NULL)")
            db.commit()

    def run_exclusive(self, operation):
        """Fail closed if writer lock unavailable; release lock on error."""
        with closing(sqlite3.connect(str(self.path), timeout=self.timeout_seconds,
                                     isolation_level=None)) as db:
            db.execute("PRAGMA busy_timeout=" + str(int(self.timeout_seconds * 1000)))
            db.execute("BEGIN IMMEDIATE")
            try:
                db.execute("INSERT OR IGNORE INTO gate_lock(id,touched) VALUES (1,0)")
                db.execute("UPDATE gate_lock SET touched=touched+1 WHERE id=1")
                result = operation()
                db.execute("COMMIT")
                return result
            except BaseException:
                db.execute("ROLLBACK")
                raise


class SerializedHistoryOperationsV1:
    """Wrap trusted existing ingress operations; never grant authority."""
    def __init__(self, *, gate: ArchiveWriteGateV1, ingress):
        self.gate = gate
        self.ingress = ingress

    def sync(self, *, payload, token):
        return self.gate.run_exclusive(
            lambda: self.ingress.sync(payload=payload, token=token, local_trusted=False))

    def owner_delete(self, *, conversation_id, project_id, token):
        return self.gate.run_exclusive(
            lambda: self.ingress.owner_delete(
                conversation_id=conversation_id, project_id=project_id, token=token))
