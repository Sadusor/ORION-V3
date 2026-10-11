"""Opt-in composition of a qualified archive boundary with its search projection.

Never changes frozen writers, memory authority or server routes. The index is
derived and can be rebuilt; the archive commit is always authoritative.
"""
from __future__ import annotations

class IndexedArchiveBoundaryV1:
    def __init__(self, *, boundary, index_sync):
        self.boundary = boundary
        self.index_sync = index_sync

    def sync(self, *, device_token, body):
        status, result = self.boundary.sync(device_token=device_token, body=body)
        if status == 200 and result.get("ok") is True:
            # Failing to update a derived index must be observable; never
            # pretend that a committed write was rolled back.
            try:
                self.index_sync.after_archive_commit()
            except Exception as error:
                return 503, {"ok": False, "archive_committed": True,
                             "index_needs_rebuild": True, "error": "index refresh failed"}
        return status, result

    def owner_delete(self, *, owner_token, conversation_id, project_id):
        status, result = self.boundary.owner_delete(
            owner_token=owner_token, conversation_id=conversation_id,
            project_id=project_id)
        if status == 200 and result.get("ok") is True:
            try:
                self.index_sync.after_owner_deletion()
            except Exception:
                return 503, {"ok": False, "deletion_committed": True,
                             "index_needs_rebuild": True, "error": "index refresh failed"}
        return status, result
