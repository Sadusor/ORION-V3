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


def build_archive_route_fixture(*, root: str | Path, project_id: str, enabled=False):
    """Build an isolated optional route, never mutate live ORION directories.

    Enablement is fixed when this fixture is created. Test-owned credentials
    must be explicitly provisioned outside this function by an authorized owner.
    """
    directory = Path(root)
    if not directory.is_dir():
        raise ValueError("An existing isolated test directory is required")
    if not isinstance(project_id, str) or not project_id.strip() or len(project_id) > 160:
        raise ValueError("Explicit bounded project is required")
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
        verify_sync_auth=lambda token: device_credentials.authorized(token, project_id),
    )
    reconcile_gate = DeviceReconcileGateV1(
        ledger=ledger, feature_enabled=active,
        project_authorized=lambda token, requested: (requested == project_id
                                                     and authorize_project(token, requested)))
    reconciled = ReconciledSyncV1(
        reconcile_gate=reconcile_gate, ingress=ingress, feature_enabled=active)
    boundary = HistoryArchiveTransactionalBoundaryV1(
        writer_gate=ArchiveWriteGateV1(directory / "archive-writer-gate.sqlite3"),
        reconciled_sync=reconciled, ingress=ingress, enabled=active)
    return HistoryArchiveRouteAdapterV1(
        boundary=boundary, enabled=active,
        project_authorized=lambda token, requested: (requested == project_id
                                                     and authorize_project(token, requested)),
        owner_authorized=owner.verify,
    )
