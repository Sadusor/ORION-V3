"""Offline-phone project reconciliation qualification; all data temporary."""
import tempfile
import unittest
from pathlib import Path

from src.orion_v3.modules.history_archive_delete_guard_v1 import OwnerDeleteLedgerV1
from src.orion_v3.modules.history_archive_device_reconcile_v1 import reconcile_project_snapshot
from src.orion_v3.modules.history_archive_client_reconcile_v1 import ReconciliationError


def snapshot(project="orion-v3"):
    return {"conversations": [
        {"id": "old", "project_id": project},
        {"id": "current", "project_id": project}],
        "messages": [
            {"id": "m-old", "conversation_id": "old", "text": "stale"},
            {"id": "m-current", "conversation_id": "current", "text": "valid"}]}


class DeviceReconcileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ledger = OwnerDeleteLedgerV1(Path(self.tmp.name) / "deletes.sqlite3")
        self.ledger.record_owner_delete(conversation_id="old", project_id="orion-v3",
                                        deleted_at_ms=100, owner_authorized=True)
        self.ledger.record_owner_delete(conversation_id="secret", project_id="other",
                                        deleted_at_ms=110, owner_authorized=True)

    def reconcile(self, s=None, project="orion-v3"):
        return reconcile_project_snapshot(
            project_id=project, snapshot=s if s is not None else snapshot(),
            ledger=self.ledger)

    def test_deleted_phone_rows_removed_preserve_current(self):
        r = self.reconcile()
        self.assertEqual([x["id"] for x in r["conversations"]], ["current"])
        self.assertEqual([x["id"] for x in r["messages"]], ["m-current"])
        self.assertEqual(r["removed_conversation_ids"], ["old"])

    def test_no_other_project_tombstone_disclosure(self):
        self.assertNotIn("secret", repr(self.reconcile()))

    def test_cross_project_snapshot_denied(self):
        with self.assertRaises(ReconciliationError):
            self.reconcile(snapshot("other"))

    def test_orphan_message_denied(self):
        s = snapshot()
        s["messages"].append({"id": "orphan", "conversation_id": "foreign"})
        with self.assertRaises(ReconciliationError):
            self.reconcile(s)

    def test_cross_project_deleted_identity_denied(self):
        s = {"conversations": [{"id": "secret", "project_id": "orion-v3"}],
             "messages": []}
        with self.assertRaises(ReconciliationError):
            self.reconcile(s)

    def test_invalid_input_denied(self):
        for s in [None, {"conversations": "bad"}, {"conversations": [{}]},
                  {"conversations": [], "messages": [{"conversation_id": "old"}]}]:
            with self.subTest(value=s), self.assertRaises(ReconciliationError):
                reconcile_project_snapshot(project_id="orion-v3", snapshot=s, ledger=self.ledger)

    def test_empty_snapshot_does_not_disclose_deleted_ids(self):
        r = self.reconcile({"conversations": [], "messages": []})
        self.assertEqual(r["removed_conversation_ids"], [])

    def test_excessive_snapshot_denied(self):
        with self.assertRaises(ReconciliationError):
            self.reconcile({"conversations": [], "messages": [{}] * 100001})


if __name__ == "__main__":
    unittest.main()
