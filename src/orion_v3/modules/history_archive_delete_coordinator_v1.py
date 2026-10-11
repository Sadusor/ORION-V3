"""Stage C2 isolated owner deletion coordinator; not connected to HTTP/UI.

The durable tombstone is written BEFORE erasing either store; on failure,
retrying the same authenticated operation completes the remaining deletes.
A shared call lock covers this coordinator instance only; an eventual live
integration must serialize all chat-sync and delete operations at ingress.
"""
from __future__ import annotations

import sqlite3
import threading
import time
from contextlib import closing
from pathlib import Path

from .history_archive_delete_guard_v1 import OwnerDeleteLedgerV1
from .history_archive_v1 import HistoryArchiveV1


class DeleteScopeConflict(RuntimeError):
    pass


class OwnerDeleteCoordinatorV1:
    def __init__(self, *, live_path: str | Path,
                 archive: HistoryArchiveV1, ledger: OwnerDeleteLedgerV1):
        self.live_path = Path(live_path)
        self.archive = archive
        self.ledger = ledger
        self._lock = threading.RLock()

    def _assert_project_matches(self, cid: str, project: str) -> None:
        with closing(sqlite3.connect(str(self.live_path), timeout=10)) as db:
            row = db.execute(
                "SELECT project_id FROM conversations WHERE id=?", (cid,)
            ).fetchone()
            if row and row[0] and row[0] != project:
                raise DeleteScopeConflict("Live conversation project mismatch")
        with closing(sqlite3.connect(str(self.archive.path), timeout=10)) as db:
            row = db.execute(
                "SELECT project_id FROM conversations WHERE id=?", (cid,)
            ).fetchone()
            if row and row[0] and row[0] != project:
                raise DeleteScopeConflict("Archive conversation project mismatch")

    def delete(self, *, conversation_id: str, project_id: str,
               owner_authorized: bool = False,
               deleted_at_ms: int | None = None) -> dict:
        if not owner_authorized:
            raise PermissionError("Only authenticated owner may delete")
        cid, project = str(conversation_id).strip(), str(project_id).strip()
        if not cid or not project or len(cid) > 120 or len(project) > 160:
            raise ValueError("Valid bounded identity required")
        timestamp = int(deleted_at_ms if deleted_at_ms is not None
                        else time.time() * 1000)
        if timestamp <= 0:
            raise ValueError("Deletion timestamp must be positive")
        with self._lock:
            # Scope check BEFORE creating the irreversible durable tombstone.
            self._assert_project_matches(cid, project)
            self.ledger.record_owner_delete(
                conversation_id=cid, project_id=project,
                deleted_at_ms=timestamp, owner_authorized=True
            )
            # A partial failure leaves the tombstone in place so stale sync
            # cannot resurrect messages; an authorized retry will finish.
            self.archive.delete_conversation(
                cid, deleted_at_ms=timestamp, owner_delete_confirmed=True
            )
            with closing(sqlite3.connect(str(self.live_path), timeout=10)) as db, db:
                db.execute("DELETE FROM messages WHERE conversation_id=?", (cid,))
                db.execute("DELETE FROM conversations WHERE id=?", (cid,))
            return {"deleted": True, "conversation_id": cid, "project_id": project}

    def guarded_sync(self, payload: dict, sync_callable):
        """Test seam; caller must also enforce this on *all* live sync paths."""
        with self._lock:
            self.ledger.reject_replays(payload)
            return sync_callable(payload)
