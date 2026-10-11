"""Inactive HistoryArchive API adapter; never registered in product_server.

All callers MUST pass a stronger project-bound credential for sync or a
separately enrolled owner credential for deletion. No loopback bypass.
This adapter is transport-neutral; HTTP wiring is a separate reviewed step.
"""
from __future__ import annotations

SYNC_PATH = "/api/history-archive/device-sync"
DELETE_PATH = "/api/history-archive/owner-delete"


class HistoryArchiveRouteAdapterV1:
    def __init__(self, *, boundary, enabled, project_authorized, owner_authorized):
        self.boundary = boundary
        self.enabled = enabled
        self.project_authorized = project_authorized
        self.owner_authorized = owner_authorized

    def dispatch(self, *, path: str, device_token: str = "",
                 owner_token: str = "", body=None):
        if path not in (SYNC_PATH, DELETE_PATH) or not self.enabled():
            return 404, {"ok": False, "error": "route disabled"}
        if not isinstance(body, dict):
            return 400, {"ok": False, "error": "invalid body"}
        project = body.get("project_id")
        if not isinstance(project, str) or not project or len(project) > 160:
            return 400, {"ok": False, "error": "invalid project"}
        if path == SYNC_PATH:
            if not device_token or not self.project_authorized(device_token, project):
                return 403, {"ok": False, "error": "project authorization required"}
            if "snapshot" not in body:
                return 400, {"ok": False, "error": "snapshot required"}
            try:
                return self.boundary.sync(device_token=device_token, body=body)
            except Exception:
                return 409, {"ok": False, "error": "archive sync incomplete"}
        cid = body.get("conversation_id")
        if not isinstance(cid, str) or not cid or len(cid) > 120:
            return 400, {"ok": False, "error": "invalid conversation"}
        if not owner_token or not self.owner_authorized(owner_token):
            return 403, {"ok": False, "error": "owner proof required"}
        try:
            return self.boundary.owner_delete(
                owner_token=owner_token, conversation_id=cid, project_id=project)
        except Exception:
            return 409, {"ok": False, "error": "owner delete incomplete"}
