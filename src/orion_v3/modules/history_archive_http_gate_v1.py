"""C4 HTTP delete boundary (not activated): separate owner proof from pairing.

The current product_server AUTH.valid() permits paired remote devices and
cannot by itself grant destructive deletion. This gate requires an independent
trusted server-side owner verifier. No client JSON field confers authority.
"""
from __future__ import annotations

from typing import Callable

from .history_archive_ingress_v1 import HistoryArchiveIngressV1


class DeleteHTTPGateV1:
    def __init__(self, ingress: HistoryArchiveIngressV1,
                 owner_proof: Callable[[str], bool],
                 feature_enabled: Callable[[], bool]):
        self.ingress = ingress
        self.owner_proof = owner_proof
        self.feature_enabled = feature_enabled

    def dispatch_delete(self, *, bearer_token: str, body: dict) -> tuple[int, dict]:
        if not self.feature_enabled():
            return 404, {"ok": False, "error": "route disabled"}
        if not isinstance(body, dict):
            return 400, {"ok": False, "error": "invalid body"}
        if not bearer_token or not self.owner_proof(bearer_token):
            return 403, {"ok": False, "error": "owner proof required"}
        cid = body.get("conversation_id")
        project = body.get("project_id")
        if (not isinstance(cid, str) or not cid.strip() or len(cid) > 120
                or not isinstance(project, str) or not project.strip()
                or len(project) > 160):
            return 400, {"ok": False, "error": "invalid conversation/project"}
        # The ingress verifier must be wired to the SAME stronger owner
        # capability, not the general pairing token validator.
        result = self.ingress.owner_delete(
            conversation_id=cid, project_id=project, token=bearer_token)
        return 200, {"ok": True, **result}
