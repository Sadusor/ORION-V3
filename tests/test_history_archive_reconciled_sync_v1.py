"""Stage C reconciled upload qualifies ordering and disabled defaults."""
import tempfile
import unittest
from pathlib import Path

from src.orion_v3.modules.history_archive_delete_guard_v1 import OwnerDeleteLedgerV1
from src.orion_v3.modules.history_archive_device_http_gate_v1 import DeviceReconcileGateV1
from src.orion_v3.modules.history_archive_reconciled_sync_v1 import ReconciledSyncV1


class FakeIngress:
    def __init__(self):
        self.written = []
        self.authorize = True
        self.fail = False

    def sync(self, *, payload, token, local_trusted):
        if not self.authorize or token != "scope-and-sync-token" or local_trusted:
            raise PermissionError("denied")
        if self.fail:
            raise RuntimeError("storage refused")
        self.written.append(payload)
        return {"accepted": True}


class ReconciledSyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        ledger = OwnerDeleteLedgerV1(Path(self.tmp.name) / "ledger.sqlite3")
        ledger.record_owner_delete(conversation_id="deleted", project_id="p",
                                   deleted_at_ms=123, owner_authorized=True)
        self.enabled = True
        self.device_gate = DeviceReconcileGateV1(
            ledger=ledger, feature_enabled=lambda: self.enabled,
            project_authorized=lambda token, project:
                token == "scope-and-sync-token" and project == "p")
        self.ingress = FakeIngress()
        self.adapter = ReconciledSyncV1(
            reconcile_gate=self.device_gate, ingress=self.ingress,
            feature_enabled=lambda: self.enabled)
        self.body = {
            "project_id": "p",
            "snapshot": {
                "conversations": [
                    {"id": "deleted", "project_id": "p"},
                    {"id": "ok", "project_id": "p"}],
                "messages": [
                    {"id": "md", "conversation_id": "deleted"},
                    {"id": "mk", "conversation_id": "ok"}]}}

    def test_disabled_no_write(self):
        self.enabled = False
        status, _ = self.adapter.dispatch(
            device_token="scope-and-sync-token", body=self.body)
        self.assertEqual(status, 404)
        self.assertEqual(self.ingress.written, [])

    def test_reconcile_before_ingress_write(self):
        status, result = self.adapter.dispatch(
            device_token="scope-and-sync-token", body=self.body)
        self.assertEqual(status, 200)
        self.assertEqual(result["removed_conversation_ids"], ["deleted"])
        self.assertEqual([r["id"] for r in self.ingress.written[0]["messages"]], ["mk"])
        self.assertEqual([r["id"] for r in self.ingress.written[0]["conversations"]], ["ok"])

    def test_generic_pair_token_denied_without_write(self):
        status, _ = self.adapter.dispatch(device_token="paired-device", body=self.body)
        self.assertEqual(status, 403)
        self.assertFalse(self.ingress.written)

    def test_ingress_auth_must_independently_allow(self):
        self.ingress.authorize = False
        status, _ = self.adapter.dispatch(
            device_token="scope-and-sync-token", body=self.body)
        self.assertEqual(status, 403)
        self.assertFalse(self.ingress.written)

    def test_other_project_denied(self):
        self.body["project_id"] = "other"
        status, _ = self.adapter.dispatch(
            device_token="scope-and-sync-token", body=self.body)
        self.assertEqual(status, 403)
        self.assertFalse(self.ingress.written)

    def test_invalid_snapshot_denied(self):
        self.body["snapshot"]["messages"].append(
            {"id": "bad", "conversation_id": "nonexistent"})
        status, _ = self.adapter.dispatch(
            device_token="scope-and-sync-token", body=self.body)
        self.assertEqual(status, 400)
        self.assertFalse(self.ingress.written)

    def test_ingress_failure_does_not_claim_success(self):
        self.ingress.fail = True
        status, result = self.adapter.dispatch(
            device_token="scope-and-sync-token", body=self.body)
        self.assertEqual(status, 409)
        self.assertFalse(result["ok"])
        self.assertFalse(self.ingress.written)

    def test_invalid_body_denied(self):
        status, _ = self.adapter.dispatch(
            device_token="scope-and-sync-token", body=None)
        self.assertEqual(status, 400)
        self.assertFalse(self.ingress.written)


if __name__ == "__main__":
    unittest.main()
