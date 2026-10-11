"""Disabled combined Stage C transaction boundary.

One shared SQLite write gate covers reconciliation, guarded sync and owner
deletion. Both operations must use this *same instance/configured gate path*.
No server routes or client credentials are enrolled here.
"""
from __future__ import annotations


class HistoryArchiveTransactionalBoundaryV1:
    def __init__(self, *, writer_gate, reconciled_sync, ingress, enabled):
        self.writer_gate = writer_gate
        self.reconciled_sync = reconciled_sync
        self.ingress = ingress
        self.enabled = enabled

    def sync(self, *, device_token: str, body: dict):
        if not self.enabled():
            return 404, {"ok": False, "error": "route disabled"}
        # Crucial: reconciliation runs INSIDE the same lock as deletion.
        return self.writer_gate.run_exclusive(
            lambda: self.reconciled_sync.dispatch(
                device_token=device_token, body=body))

    def owner_delete(self, *, owner_token: str, conversation_id: str,
                     project_id: str):
        if not self.enabled():
            return 404, {"ok": False, "error": "route disabled"}
        if not owner_token:
            return 403, {"ok": False, "error": "owner proof required"}
        try:
            result = self.writer_gate.run_exclusive(
                lambda: self.ingress.owner_delete(
                    conversation_id=conversation_id,
                    project_id=project_id, token=owner_token))
        except PermissionError:
            return 403, {"ok": False, "error": "owner proof required"}
        except Exception:
            return 409, {"ok": False, "error": "owner delete incomplete"}
        return 200, {"ok": True, **result}
