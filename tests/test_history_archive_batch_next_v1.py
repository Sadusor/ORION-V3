"""Batch qualification: offline replay reconciliation and known client source constraints."""
import tempfile
import unittest
from pathlib import Path

from src.orion_v3.modules.history_archive_client_reconcile_v1 import (
    reconcile_client_snapshot, ReconciliationError,
)
from src.orion_v3.modules.history_archive_v1 import HistoryArchiveV1


class ClientReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = {"schema": "orion.chat-history/1",
                         "conversations": [
                             {"id": "deleted", "project_id": "orion-v3"},
                             {"id": "active", "project_id": "orion-v3"}],
                         "messages": [
                             {"id": "m1", "conversation_id": "deleted"},
                             {"id": "m2", "conversation_id": "active"}]}
        self.tombstones = [{"conversation_id": "deleted",
                            "project_id": "orion-v3", "deleted_at_ms": 100}]

    def test_offline_deleted_conversation_cannot_be_resent(self):
        result = reconcile_client_snapshot(self.snapshot, self.tombstones)
        self.assertEqual([x["id"] for x in result["conversations"]], ["active"])
        self.assertEqual([x["id"] for x in result["messages"]], ["m2"])

    def test_message_only_stale_replay_filtered(self):
        snap = {"conversations": [], "messages": [{"conversation_id": "deleted"}]}
        self.assertEqual(reconcile_client_snapshot(snap, self.tombstones)["messages"], [])

    def test_unknown_tombstone_does_not_erase_unrelated_history(self):
        clean = reconcile_client_snapshot(self.snapshot, [
            {"conversation_id": "other", "project_id": "orion-v3"}])
        self.assertEqual(len(clean["conversations"]), 2)

    def test_project_collision_refused(self):
        self.snapshot["conversations"][0]["project_id"] = "other"
        with self.assertRaises(ReconciliationError):
            reconcile_client_snapshot(self.snapshot, self.tombstones)

    def test_invalid_tombstone_fails_closed(self):
        with self.assertRaises(ReconciliationError):
            reconcile_client_snapshot(self.snapshot, [{"conversation_id": "deleted"}])

    def test_permanent_archive_preserves_complete_original_message(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = HistoryArchiveV1(root / "archive.sqlite3")
            text = "Greek ελληνικά " * 1000
            data = {"conversations": [{"id": "long", "project_id": "orion-v3",
                                       "created_at_ms": 1, "updated_at_ms": 2}],
                    "messages": [{"id": "m1", "conversation_id": "long",
                                  "role": "user", "created_at_ms": 2, "text": text}]}
            archive.append_batch(data["conversations"], data["messages"])
            self.assertEqual(archive.query(project_id="orion-v3")[0]["text"], text)


if __name__ == "__main__":
    unittest.main()
