"""Stage C3 isolated ingress contract, NOT installed as a live route.

Owner deletion needs a verified paired-owner credential even on loopback.
Regular chat sync cannot derive deletion authority from client metadata.
"""
from __future__ import annotations

import threading

from .history_archive_delete_coordinator_v1 import OwnerDeleteCoordinatorV1
from .history_archive_sync_v1 import archive_first_sync


class OwnerIngressDenied(PermissionError):
    pass


class HistoryArchiveIngressV1:
    def __init__(self, *, coordinator: OwnerDeleteCoordinatorV1, archive,
                 live_sync, verify_owner_token, verify_sync_auth):
        self.coordinator = coordinator
        self.archive = archive
        self.live_sync = live_sync
        self.verify_owner_token = verify_owner_token
        self.verify_sync_auth = verify_sync_auth
        self._lock = threading.RLock()

    def sync(self, *, payload, token: str, local_trusted: bool = False):
        if not (local_trusted or self.verify_sync_auth(token)):
            raise OwnerIngressDenied("Chat sync requires authentication")
        with self._lock:
            # Guard before either database receives stale replayed messages.
            return self.coordinator.guarded_sync(
                payload, lambda data: archive_first_sync(
                    data, archive=self.archive, live_sync=self.live_sync
                )
            )

    def owner_delete(self, *, conversation_id: str, project_id: str,
                     token: str, deleted_at_ms: int | None = None):
        if not token or not self.verify_owner_token(token):
            raise OwnerIngressDenied("Paired owner token is mandatory, including loopback")
        with self._lock:
            return self.coordinator.delete(
                conversation_id=conversation_id,
                project_id=project_id,
                deleted_at_ms=deleted_at_ms,
                owner_authorized=True,
            )
