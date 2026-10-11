"""Stage C3 auth and replay integration tests, disposable files only."""
import tempfile
import unittest
from pathlib import Path

from src.orion_v3.modules.chat_history import ChatHistoryStore
from src.orion_v3.modules.history_archive_v1 import HistoryArchiveV1
from src.orion_v3.modules.history_archive_delete_guard_v1 import OwnerDeleteLedgerV1, DeletedConversationReplay
from src.orion_v3.modules.history_archive_delete_coordinator_v1 import OwnerDeleteCoordinatorV1
from src.orion_v3.modules.history_archive_ingress_v1 import HistoryArchiveIngressV1, OwnerIngressDenied


class IngressTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.live = ChatHistoryStore(root / "live.sqlite3")
        archive = HistoryArchiveV1(root / "archive.sqlite3")
        ledger = OwnerDeleteLedgerV1(root / "ledger.sqlite3")
        coord = OwnerDeleteCoordinatorV1(live_path=self.live.path,
                                         archive=archive, ledger=ledger)
        self.ingress = HistoryArchiveIngressV1(
            coordinator=coord, archive=archive, live_sync=self.live.sync,
            verify_owner_token=lambda token: token == "owner-secret",
            verify_sync_auth=lambda token: token in ("owner-secret", "paired-device"))
        self.payload = {"conversations": [{
            "id": "c1", "project_id": "orion-v3", "title": "Test",
            "created_at_ms": 100, "updated_at_ms": 200}],
            "messages": [{"id": "m1", "conversation_id": "c1", "role": "user",
                          "text": "Original", "created_at_ms": 150}]}

    def test_remote_sync_requires_valid_pairing(self):
        with self.assertRaises(OwnerIngressDenied):
            self.ingress.sync(payload=self.payload, token="")
        self.assertFalse(self.live.snapshot()["messages"])

    def test_paired_device_can_sync_but_cannot_delete(self):
        self.ingress.sync(payload=self.payload, token="paired-device")
        with self.assertRaises(OwnerIngressDenied):
            self.ingress.owner_delete(conversation_id="c1",
                project_id="orion-v3", token="paired-device")
        self.assertEqual(len(self.live.snapshot()["messages"]), 1)

    def test_loopback_does_not_bypass_owner_delete_auth(self):
        self.ingress.sync(payload=self.payload, token="", local_trusted=True)
        with self.assertRaises(OwnerIngressDenied):
            self.ingress.owner_delete(conversation_id="c1",
                project_id="orion-v3", token="")
        self.assertEqual(len(self.live.snapshot()["messages"]), 1)

    def test_owner_deletes_both_and_replay_denied(self):
        self.ingress.sync(payload=self.payload, token="paired-device")
        self.ingress.owner_delete(conversation_id="c1", project_id="orion-v3",
                                  token="owner-secret", deleted_at_ms=300)
        self.assertFalse(self.live.snapshot()["messages"])
        with self.assertRaises(DeletedConversationReplay):
            self.ingress.sync(payload=self.payload, token="paired-device")

    def test_message_only_replay_is_rejected(self):
        self.ingress.sync(payload=self.payload, token="owner-secret")
        self.ingress.owner_delete(conversation_id="c1", project_id="orion-v3",
                                  token="owner-secret", deleted_at_ms=300)
        with self.assertRaises(DeletedConversationReplay):
            self.ingress.sync(payload={"conversations": [],
                                     "messages": self.payload["messages"]},
                              token="owner-secret")

    def test_metadata_delete_flag_cannot_authorize_owner_delete(self):
        self.payload["conversations"][0]["deleted"] = 1
        with self.assertRaises(Exception):
            self.ingress.sync(payload=self.payload, token="paired-device")
        self.assertEqual(self.ingress.coordinator.ledger.tombstones(), [])


if __name__ == "__main__":
    unittest.main()
