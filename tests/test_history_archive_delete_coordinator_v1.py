"""Stage C2 delete-saga tests; only temporary SQLite files."""
import tempfile
import unittest
from pathlib import Path

from src.orion_v3.modules.chat_history import ChatHistoryStore
from src.orion_v3.modules.history_archive_v1 import HistoryArchiveV1
from src.orion_v3.modules.history_archive_delete_guard_v1 import (
    OwnerDeleteLedgerV1, DeletedConversationReplay,
)
from src.orion_v3.modules.history_archive_delete_coordinator_v1 import (
    OwnerDeleteCoordinatorV1, DeleteScopeConflict,
)


class CoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.live = ChatHistoryStore(root / "live.sqlite3")
        self.archive = HistoryArchiveV1(root / "archive.sqlite3")
        self.ledger = OwnerDeleteLedgerV1(root / "ledger.sqlite3")
        self.coordinator = OwnerDeleteCoordinatorV1(
            live_path=self.live.path, archive=self.archive, ledger=self.ledger)
        self.payload = {
            "conversations": [{"id": "c1", "project_id": "orion-v3",
                               "title": "Test", "created_at_ms": 1000,
                               "updated_at_ms": 2000}],
            "messages": [{"id": "m1", "conversation_id": "c1", "role": "user",
                          "created_at_ms": 1100, "text": "Secret"}]}
        self.live.sync(self.payload)
        self.archive.append_batch(self.payload["conversations"],
                                  self.payload["messages"])

    def test_deletes_both_and_blocks_stale_sync(self):
        self.coordinator.delete(conversation_id="c1", project_id="orion-v3",
                                owner_authorized=True, deleted_at_ms=3000)
        self.assertFalse(self.live.snapshot()["messages"])
        self.assertFalse(self.archive.query(project_id="orion-v3"))
        with self.assertRaises(DeletedConversationReplay):
            self.coordinator.guarded_sync(self.payload, self.live.sync)

    def test_no_auth_does_not_delete(self):
        with self.assertRaises(PermissionError):
            self.coordinator.delete(conversation_id="c1", project_id="orion-v3")
        self.assertEqual(len(self.live.snapshot()["messages"]), 1)
        self.assertFalse(self.ledger.tombstones())

    def test_wrong_project_cannot_tombstone(self):
        with self.assertRaises(DeleteScopeConflict):
            self.coordinator.delete(conversation_id="c1", project_id="other",
                                    owner_authorized=True)
        self.assertFalse(self.ledger.tombstones())
        self.assertEqual(len(self.archive.query(project_id="orion-v3")), 1)

    def test_retry_completes_after_archive_failure(self):
        original = self.archive.delete_conversation
        def broken(*args, **kwargs):
            raise OSError("simulated interruption")
        self.archive.delete_conversation = broken
        with self.assertRaises(OSError):
            self.coordinator.delete(conversation_id="c1", project_id="orion-v3",
                                    owner_authorized=True, deleted_at_ms=3000)
        self.assertEqual(len(self.ledger.tombstones()), 1)
        with self.assertRaises(DeletedConversationReplay):
            self.coordinator.guarded_sync(self.payload, self.live.sync)
        self.archive.delete_conversation = original
        self.coordinator.delete(conversation_id="c1", project_id="orion-v3",
                                owner_authorized=True, deleted_at_ms=3000)
        self.assertFalse(self.archive.query(project_id="orion-v3"))
        self.assertFalse(self.live.snapshot()["messages"])

    def test_restart_retry_is_idempotent(self):
        self.coordinator.delete(conversation_id="c1", project_id="orion-v3",
                                owner_authorized=True, deleted_at_ms=3000)
        again = OwnerDeleteCoordinatorV1(
            live_path=self.live.path, archive=HistoryArchiveV1(self.archive.path),
            ledger=OwnerDeleteLedgerV1(self.ledger.path))
        again.delete(conversation_id="c1", project_id="orion-v3",
                     owner_authorized=True, deleted_at_ms=3000)
        self.assertEqual(len(self.ledger.tombstones()), 1)

    def test_message_only_stale_replay_is_blocked(self):
        self.coordinator.delete(conversation_id="c1", project_id="orion-v3",
                                owner_authorized=True, deleted_at_ms=3000)
        with self.assertRaises(DeletedConversationReplay):
            self.coordinator.guarded_sync({"conversations": [],
                    "messages": self.payload["messages"]}, self.live.sync)


if __name__ == "__main__":
    unittest.main()
