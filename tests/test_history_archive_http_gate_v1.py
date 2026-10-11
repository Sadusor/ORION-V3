"""C4 HTTP gate tests: no live route, only temp SQLite."""
import tempfile
import unittest
from pathlib import Path
from src.orion_v3.modules.chat_history import ChatHistoryStore
from src.orion_v3.modules.history_archive_v1 import HistoryArchiveV1
from src.orion_v3.modules.history_archive_delete_guard_v1 import OwnerDeleteLedgerV1
from src.orion_v3.modules.history_archive_delete_coordinator_v1 import OwnerDeleteCoordinatorV1
from src.orion_v3.modules.history_archive_ingress_v1 import HistoryArchiveIngressV1
from src.orion_v3.modules.history_archive_http_gate_v1 import DeleteHTTPGateV1


class HTTPGateTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        self.live = ChatHistoryStore(root / "live.sqlite3")
        archive = HistoryArchiveV1(root / "archive.sqlite3")
        ledger = OwnerDeleteLedgerV1(root / "ledger.sqlite3")
        coordinator = OwnerDeleteCoordinatorV1(
            live_path=self.live.path, archive=archive, ledger=ledger)
        self.payload = {"conversations": [{"id": "c1", "project_id": "orion-v3",
                                            "created_at_ms": 10, "updated_at_ms": 20}],
                        "messages": [{"id": "m1", "conversation_id": "c1",
                                      "role": "user", "text": "Private",
                                      "created_at_ms": 15}]}
        self.live.sync(self.payload)
        archive.append_batch(self.payload["conversations"], self.payload["messages"])
        ingress = HistoryArchiveIngressV1(
            coordinator=coordinator, archive=archive, live_sync=self.live.sync,
            verify_owner_token=lambda token: token == "independent-owner",
            verify_sync_auth=lambda token: token in ("paired-device", "independent-owner"))
        self.enabled = False
        self.gate = DeleteHTTPGateV1(
            ingress, lambda token: token == "independent-owner",
            lambda: self.enabled)

    def request(self, token="independent-owner", body=None):
        return self.gate.dispatch_delete(
            bearer_token=token,
            body={"conversation_id": "c1", "project_id": "orion-v3"}
                 if body is None else body)

    def test_disabled_route_is_not_reachable(self):
        self.assertEqual(self.request()[0], 404)
        self.assertEqual(len(self.live.snapshot()["messages"]), 1)

    def test_paired_device_is_not_owner(self):
        self.enabled = True
        self.assertEqual(self.request("paired-device")[0], 403)
        self.assertEqual(len(self.live.snapshot()["messages"]), 1)

    def test_blank_token_is_denied(self):
        self.enabled = True
        self.assertEqual(self.request("")[0], 403)

    def test_client_supplied_owner_flag_is_ignored(self):
        self.enabled = True
        body = {"conversation_id": "c1", "project_id": "orion-v3",
                "owner_authorized": True, "local_trusted": True}
        self.assertEqual(self.request("paired-device", body)[0], 403)

    def test_invalid_body_does_not_delete(self):
        self.enabled = True
        self.assertEqual(self.request(body={"conversation_id": "c1"})[0], 400)
        self.assertEqual(len(self.live.snapshot()["messages"]), 1)

    def test_independent_owner_proof_deletes_and_blocks_replay(self):
        self.enabled = True
        code, result = self.request()
        self.assertEqual(code, 200)
        self.assertTrue(result["deleted"])
        self.assertFalse(self.live.snapshot()["messages"])
        from src.orion_v3.modules.history_archive_delete_guard_v1 import DeletedConversationReplay
        with self.assertRaises(DeletedConversationReplay):
            self.gate.ingress.sync(payload=self.payload, token="paired-device")


if __name__ == "__main__":
    unittest.main()
