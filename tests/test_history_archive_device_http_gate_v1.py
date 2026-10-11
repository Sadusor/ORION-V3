"""Qualification of disabled Stage C device HTTP adapter."""
import tempfile
import unittest
from pathlib import Path
from src.orion_v3.modules.history_archive_delete_guard_v1 import OwnerDeleteLedgerV1
from src.orion_v3.modules.history_archive_device_http_gate_v1 import DeviceReconcileGateV1


class DeviceHTTPGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        ledger = OwnerDeleteLedgerV1(Path(self.tmp.name) / "ledger.sqlite3")
        ledger.record_owner_delete(conversation_id="old", project_id="orion-v3",
                                   deleted_at_ms=100, owner_authorized=True)
        self.calls = []
        def authorize(token, project):
            self.calls.append((token, project))
            return token == "scoped-token" and project == "orion-v3"
        self.enabled = True
        self.gate = DeviceReconcileGateV1(
            ledger=ledger, feature_enabled=lambda: self.enabled,
            project_authorized=authorize)
        self.body = {"project_id": "orion-v3", "snapshot": {
            "conversations": [{"id": "old", "project_id": "orion-v3"},
                              {"id": "new", "project_id": "orion-v3"}],
            "messages": [{"id": "m1", "conversation_id": "old"},
                         {"id": "m2", "conversation_id": "new"}]}}

    def test_disabled_fails_closed(self):
        self.enabled = False
        status, result = self.gate.dispatch(device_token="scoped-token", body=self.body)
        self.assertEqual(status, 404)
        self.assertEqual(self.calls, [])

    def test_missing_token_denied(self):
        status, _ = self.gate.dispatch(device_token="", body=self.body)
        self.assertEqual(status, 403)
        self.assertEqual(self.calls, [])

    def test_pairing_token_does_not_grant_scope(self):
        status, _ = self.gate.dispatch(device_token="paired-device", body=self.body)
        self.assertEqual(status, 403)

    def test_foreign_project_denied(self):
        body = dict(self.body, project_id="other")
        status, _ = self.gate.dispatch(device_token="scoped-token", body=body)
        self.assertEqual(status, 403)

    def test_authorized_filters_stale_rows(self):
        status, result = self.gate.dispatch(device_token="scoped-token", body=self.body)
        self.assertEqual(status, 200)
        snap = result["snapshot"]
        self.assertEqual([x["id"] for x in snap["conversations"]], ["new"])
        self.assertEqual([x["id"] for x in snap["messages"]], ["m2"])
        self.assertEqual(snap["removed_conversation_ids"], ["old"])

    def test_cross_project_snapshot_denied(self):
        self.body["snapshot"]["conversations"][0]["project_id"] = "other"
        status, _ = self.gate.dispatch(device_token="scoped-token", body=self.body)
        self.assertEqual(status, 400)

    def test_malformed_snapshot_denied(self):
        status, _ = self.gate.dispatch(
            device_token="scoped-token",
            body={"project_id": "orion-v3", "snapshot": None})
        self.assertEqual(status, 400)

    def test_invalid_body_denied(self):
        status, _ = self.gate.dispatch(device_token="scoped-token", body=[])
        self.assertEqual(status, 400)


if __name__ == "__main__":
    unittest.main()
