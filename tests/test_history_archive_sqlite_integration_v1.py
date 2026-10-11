"""Stage C offline end-to-end fixture: actual SQLite stores, no server activation."""
import tempfile
import unittest
from pathlib import Path

from src.orion_v3.modules.chat_history import ChatHistoryStore
from src.orion_v3.modules.history_archive_v1 import HistoryArchiveV1
from src.orion_v3.modules.history_archive_delete_guard_v1 import OwnerDeleteLedgerV1
from src.orion_v3.modules.history_archive_delete_coordinator_v1 import OwnerDeleteCoordinatorV1
from src.orion_v3.modules.history_archive_ingress_v1 import HistoryArchiveIngressV1
from src.orion_v3.modules.history_archive_device_http_gate_v1 import DeviceReconcileGateV1
from src.orion_v3.modules.history_archive_reconciled_sync_v1 import ReconciledSyncV1
from src.orion_v3.modules.history_archive_write_gate_v1 import ArchiveWriteGateV1
from src.orion_v3.modules.history_archive_transactional_boundary_v1 import HistoryArchiveTransactionalBoundaryV1


def snapshot():
    return {"schema": "orion.chat-history/1",
            "conversations": [{"id": "old", "project_id": "orion-v3", "created_at_ms": 1,
                               "updated_at_ms": 100}],
            "messages": [{"id": "old-m", "conversation_id": "old", "role": "user",
                          "text": "full permanent memory " * 700, "created_at_ms": 10}]}


class RealSQLiteEndToEnd(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.live = ChatHistoryStore(root / "live.sqlite3")
        self.archive = HistoryArchiveV1(root / "archive.sqlite3")
        self.ledger = OwnerDeleteLedgerV1(root / "delete.sqlite3")
        self.coord = OwnerDeleteCoordinatorV1(live_path=self.live.path,
                                               archive=self.archive, ledger=self.ledger)
        ingress = HistoryArchiveIngressV1(
            coordinator=self.coord, archive=self.archive, live_sync=self.live.sync,
            verify_owner_token=lambda s: s == "independent-owner",
            verify_sync_auth=lambda s: s == "scoped-device")
        device = DeviceReconcileGateV1(
            ledger=self.ledger, feature_enabled=lambda: True,
            project_authorized=lambda token, project:
                token == "scoped-device" and project == "orion-v3")
        reconciled = ReconciledSyncV1(
            reconcile_gate=device, ingress=ingress, feature_enabled=lambda: True)
        self.enabled = True
        self.boundary = HistoryArchiveTransactionalBoundaryV1(
            writer_gate=ArchiveWriteGateV1(root / "shared-gate.sqlite3"),
            reconciled_sync=reconciled, ingress=ingress,
            enabled=lambda: self.enabled)

    def test_roundtrip_archive_then_delete_then_offline_replay_filtered(self):
        original = snapshot()
        self.assertEqual(self.boundary.sync(
            device_token="scoped-device",
            body={"project_id": "orion-v3", "snapshot": original})[0], 200)
        archived = self.archive.query(project_id="orion-v3")
        self.assertEqual(archived[0]["text"], original["messages"][0]["text"])
        self.assertLess(len(self.live.snapshot()["messages"][0]["text"]),
                        len(original["messages"][0]["text"]))
        self.assertEqual(self.boundary.owner_delete(
            owner_token="independent-owner", conversation_id="old",
            project_id="orion-v3")[0], 200)
        self.assertEqual(self.archive.query(project_id="orion-v3"), [])
        self.assertEqual(self.live.snapshot()["messages"], [])
        status, response = self.boundary.sync(
            device_token="scoped-device",
            body={"project_id": "orion-v3", "snapshot": original})
        self.assertEqual(status, 200)
        self.assertEqual(response["removed_conversation_ids"], ["old"])
        self.assertEqual(self.archive.query(project_id="orion-v3"), [])
        self.assertEqual(self.live.snapshot()["messages"], [])

    def test_pairing_token_cannot_reconcile_or_delete(self):
        self.assertEqual(self.boundary.sync(
            device_token="ordinary-pair", body={"project_id": "orion-v3",
                                                  "snapshot": snapshot()})[0], 403)
        self.assertEqual(self.boundary.owner_delete(
            owner_token="ordinary-pair", conversation_id="old",
            project_id="orion-v3")[0], 403)
        self.assertEqual(self.archive.query(project_id="orion-v3"), [])

    def test_disabled_does_not_write(self):
        self.enabled = False
        self.assertEqual(self.boundary.sync(
            device_token="scoped-device", body={"project_id": "orion-v3",
                                                  "snapshot": snapshot()})[0], 404)
        self.assertEqual(self.archive.query(project_id="orion-v3"), [])

    def test_project_scope_fails_closed(self):
        original = snapshot()
        original["conversations"][0]["project_id"] = "another"
        self.assertEqual(self.boundary.sync(
            device_token="scoped-device",
            body={"project_id": "orion-v3", "snapshot": original})[0], 400)
        self.assertEqual(self.archive.query(project_id="orion-v3"), [])


if __name__ == "__main__":
    unittest.main()
