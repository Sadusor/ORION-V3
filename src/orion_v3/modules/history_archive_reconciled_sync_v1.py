"""Experimental device reconciled-sync adapter, not installed in product server.

Uses the frozen Stage C project-authorized reconciliation gate, then the
existing guarded ingress sync. Never writes deleted rows into archive/live.
This instance lock does NOT replace process-wide sync/delete serialization.
"""
from __future__ import annotations

import threading


class ReconciledSyncV1:
    def __init__(self, *, reconcile_gate, ingress, feature_enabled):
        self.reconcile_gate = reconcile_gate
        self.ingress = ingress
        self.feature_enabled = feature_enabled
        self._lock = threading.RLock()

    def dispatch(self, *, device_token: str, body: dict) -> tuple[int, dict]:
        if not self.feature_enabled():
            return 404, {"ok": False, "error": "route disabled"}
        if not isinstance(body, dict):
            return 400, {"ok": False, "error": "invalid request"}
        with self._lock:
            status, result = self.reconcile_gate.dispatch(
                device_token=device_token, body=body
            )
            if status != 200:
                return status, result
            safe = result["snapshot"]
            try:
                # The ingress must verify sync authentication independently and
                # run replay protection before either persistent store is written.
                synced = self.ingress.sync(
                    payload=safe, token=device_token, local_trusted=False
                )
            except PermissionError:
                return 403, {"ok": False, "error": "sync authorization required"}
            except Exception as exc:
                # Do not leak internal store details over the HTTP boundary.
                return 409, {"ok": False, "error": "guarded sync did not complete"}
            return 200, {"ok": True, "sync": synced,
                         "removed_conversation_ids": safe["removed_conversation_ids"]}
