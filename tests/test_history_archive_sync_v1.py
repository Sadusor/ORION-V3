"""Stage B integration tests; never touch a production database."""
import tempfile
import unittest
from pathlib import Path

from src.orion_v3.modules.chat_history import ChatHistoryStore
from src.orion_v3.modules.history_archive_v1 import HistoryArchiveV1
from src.orion_v3.modules.history_archive_sync_v1 import (
    ArchiveSyncHold, archive_first_sync
)


class HistoryArchiveSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.live = ChatHistoryStore(root / "live.sqlite3")
        self.archive = HistoryArchiveV1(root / "archive.sqlite3")

    @staticmethod
    def payload(*, deleted=False, project="orion-v3", text="original"):
        return {
            "conversations": [{
                "id": "test-conversation", "title": "Test", "project_id": project,
                "created_at_ms": 1000, "updated_at_ms": 3000,
                "deleted": int(deleted),
            }],
            "messages": [{
                "id": "test-message", "conversation_id": "test-conversation",
                "role": "user", "text": text, "created_at_ms": 2000
            }],
        }

    def test_archive_first_and_live_sync(self):
        result = archive_first_sync(
            self.payload(text="Z" * 8200),
            archive=self.archive,
            live_sync=self.live.sync,
        )
        self.assertEqual(len(result["messages"]), 1)
        self.assertEqual(len(result["messages"][0]["text"]), 8000)
        rows = self.archive.query(project_id="orion-v3")
        self.assertEqual(rows[0]["text"], "Z" * 8200)

    def test_delete_flag_refused_without_modification(self):
        with self.assertRaises(ArchiveSyncHold):
            archive_first_sync(
                self.payload(deleted=True),
                archive=self.archive, live_sync=self.live.sync
            )
        self.assertEqual(self.live.snapshot()["messages"], [])
        self.assertEqual(self.archive.query(project_id="orion-v3"), [])

    def test_missing_project_refused(self):
        with self.assertRaises(ArchiveSyncHold):
            archive_first_sync(
                self.payload(project=""),
                archive=self.archive, live_sync=self.live.sync
            )
        self.assertEqual(self.live.snapshot()["messages"], [])

    def test_archive_failure_does_not_call_live(self):
        called = []
        payload = self.payload()
        payload["messages"][0]["role"] = "invalid"
        with self.assertRaises(ValueError):
            archive_first_sync(payload, archive=self.archive,
                               live_sync=lambda p: called.append(p))
        self.assertFalse(called)

    def test_resync_is_idempotent(self):
        payload = self.payload()
        archive_first_sync(payload, archive=self.archive, live_sync=self.live.sync)
        archive_first_sync(payload, archive=self.archive, live_sync=self.live.sync)
        self.assertEqual(len(self.archive.query(project_id="orion-v3")), 1)
        self.assertEqual(len(self.live.snapshot()["messages"]), 1)


if __name__ == "__main__":
    unittest.main()
