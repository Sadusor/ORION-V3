"""Stage C device reconciliation HTTP adapter. Not routed or enabled.

Caller must authenticate the device AND authorize project scope before invoking.
This adapter cannot delete conversations or enroll owner credentials.
"""
from __future__ import annotations

from collections.abc import Callable

from .history_archive_device_reconcile_v1 import reconcile_project_snapshot
from .history_archive_client_reconcile_v1 import ReconciliationError


class DeviceReconcileGateV1:
    def __init__(self, *, ledger, feature_enabled: Callable[[], bool],
                 project_authorized: Callable[[str, str], bool]):
        self.ledger = ledger
        self.feature_enabled = feature_enabled
        self.project_authorized = project_authorized

    def dispatch(self, *, device_token: str, body: dict) -> tuple[int, dict]:
        if not self.feature_enabled():
            return 404, {"ok": False, "error": "route disabled"}
        if not isinstance(body, dict):
            return 400, {"ok": False, "error": "invalid request"}
        project = body.get("project_id")
        if not isinstance(project, str) or not project.strip() or len(project) > 160:
            return 400, {"ok": False, "error": "invalid project"}
        if not isinstance(device_token, str) or not device_token:
            return 403, {"ok": False, "error": "device project authorization required"}
        # An explicit token+project verifier is necessary: a generic pairing
        # token must never imply access to arbitrary project history.
        if not self.project_authorized(device_token, project):
            return 403, {"ok": False, "error": "device project authorization required"}
        try:
            result = reconcile_project_snapshot(
                project_id=project, snapshot=body.get("snapshot"), ledger=self.ledger
            )
        except ReconciliationError:
            return 400, {"ok": False, "error": "invalid project snapshot"}
        return 200, {"ok": True, "snapshot": result}
