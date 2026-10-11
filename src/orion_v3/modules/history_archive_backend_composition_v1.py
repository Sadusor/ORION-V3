"""Nonproduction composition of the already-qualified HistoryArchive modules.

Nothing in this file registers HTTP handlers or activates a server feature.
All storage roots and enablement must be supplied explicitly by a caller.
Only the independent credentials can authorize project-scoped archive access.
"""
from __future__ import annotations

from pathlib import Path

from .chat_history import ChatHistoryStore
from .history_archive_v1 import HistoryArchiveV1
from .history_archive_delete_guard_v1 import OwnerDeleteLedgerV1
from .history_archive_delete_coordinator_v1 import OwnerDeleteCoordinatorV1
from .history_archive_ingress_v1 import HistoryArchiveIngressV1
from .history_archive_device_http_gate_v1 import DeviceReconcileGateV1
from .history_archive_reconciled_sync_v1 import ReconciledSyncV1
from .history_archive_write_gate_v1 import ArchiveWriteGateV1
from .history_archive_transactional_boundary_v1 import HistoryArchiveTransactionalBoundaryV1
from .history_archive_route_adapter_v1 import HistoryArchiveRouteAdapterV1
from .history_archive_scoped_credentials_v1 import ProjectDeviceCredentialsV1
from .history_archive_owner_capability_v1 import OwnerCapabilityV1


def build_archive_route_fixture(*, root: str | Path, enabled=False):
    """Build an isolated optional route, never mutate live ORION directories.

    Enablement is fixed when this fixture is created. Test-owned credentials
    must be explicitly provisioned outside this function by an authorized owner.
    """
    directory = Path(root)
    if not directory.is_dir():
        raise ValueError("An existing isolated test directory is required")
    if enabled is not True and enabled is not False:
        raise ValueError("Explicit boolean enablement required")
    active = lambda: enabled is True
    device_credentials = ProjectDeviceCredentialsV1(directory / "device-credentials.sqlite3")
    owner = OwnerCapabilityV1(directory / "owner-capability")
    archive = HistoryArchiveV1(directory / "archive.sqlite3")
    ledger = OwnerDeleteLedgerV1(directory / "owner-deletions.sqlite3")
    live = ChatHistoryStore(directory / "live.sqlite3")
    authorize_project = device_credentials.authorized
    ingress = HistoryArchiveIngressV1(
        coordinator=OwnerDeleteCoordinatorV1(
            live_path=live.path, archive=archive, ledger=ledger),
        archive=archive, live_sync=live.sync,
        verify_owner_token=owner.verify,
        verify_sync_auth=lambda token: False,
    )
    # Sync authorization is also project-specific. Ingress sees only the token,
    # so the device gate checks project first; ingress verifies enrollment.
    # Check against registered non-revoked credentials without using pairing.
    def any_enrolled_device(token):
        if not isinstance(token, str) or len(token) < 32:
            return False
        # Avoid authorizing a token from a different project: this verifier
        # cannot safely infer a project, so it is intentionally deny-all.
        return False

    ingress.verify_sync_auth = any_enrolled_device
    reconcile_gate = DeviceReconcileGateV1(
        ledger=ledger, feature_enabled=active,
        project_authorized=authorize_project)
    reconciled = ReconciledSyncV1(
        reconcile_gate=reconcile_gate, ingress=ingress, feature_enabled=active)
    boundary = HistoryArchiveTransactionalBoundaryV1(
        writer_gate=ArchiveWriteGateV1(directory / "archive-writer-gate.sqlite3"),
        reconciled_sync=reconciled, ingress=ingress, enabled=active)
    return HistoryArchiveRouteAdapterV1(
        boundary=boundary, enabled=active, project_authorized=authorize_project,
        owner_authorized=owner.verify,
    )
