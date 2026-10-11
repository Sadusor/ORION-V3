"""Isolated HistoryArchive V1 tests. No live deployment."""
import json
import tempfile
import unittest
from pathlib import Path

from src.orion_v3.modules.history_archive_v1 import HistoryArchiveV1, ArchiveConflict


class HistoryArchiveV1Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "archive.sqlite3"
        self.arc = HistoryArchiveV1(self.path)

    def payload(self, cid="chat-a", mid="message-a", project="alpha", text="saved"):
        return ([{"id": cid, "project_id": project}],
                [{"id": mid, "conversation_id": cid, "role": "user",
                  "created_at_ms": 123456789, "text": text, "source": "phone"}])

    def test_idempotent_and_restart(self):
        cs, ms = self.payload()
        self.assertEqual(self.arc.append_batch(cs, ms)["inserted"], 1)
        self.assertEqual(self.arc.append_batch(cs, ms)["inserted"], 0)
        reopened = HistoryArchiveV1(self.path)
        self.assertEqual(len(reopened.query(project_id="alpha")), 1)

    def test_store_untruncated_original_text(self):
        long = "α" * 8200
        cs, ms = self.payload(text=long)
        self.arc.append_batch(cs, ms)
        self.assertEqual(self.arc.query(project_id="alpha")[0]["text"], long)

    def test_delete_tombstone_prevents_replay(self):
        cs, ms = self.payload()
        self.arc.append_batch(cs, ms)
        with self.assertRaises(PermissionError):
            self.arc.delete_conversation("chat-a", deleted_at_ms=222)
        self.arc.delete_conversation("chat-a", deleted_at_ms=222,
                                     owner_delete_confirmed=True)
        self.assertEqual(self.arc.query(project_id="alpha"), [])
        self.arc.append_batch(cs, ms)
        self.assertEqual(self.arc.query(project_id="alpha"), [])

    def test_project_isolation_and_collision(self):
        cs, ms = self.payload()
        self.arc.append_batch(cs, ms)
        self.assertEqual(self.arc.query(project_id="beta"), [])
        with self.assertRaises(ArchiveConflict):
            self.arc.append_batch(*self.payload(project="beta"))
        with self.assertRaises(ArchiveConflict):
            self.arc.append_batch(*self.payload(text="tampered"))

    def test_atomic_failure_and_export(self):
        cs, ms = self.payload()
        bad = {**ms[0], "id": "bad", "role": "other"}
        with self.assertRaises(ValueError):
            self.arc.append_batch(cs, ms + [bad])
        self.assertEqual(self.arc.query(project_id="alpha"), [])
        self.arc.append_batch(cs, ms)
        data = json.loads(self.arc.export_conversation(
            project_id="alpha", conversation_id="chat-a"))
        self.assertEqual(data["messages"][0]["text"], "saved")

    def test_archive_not_affected_by_live_pruning(self):
        for i in range(120):
            cs, ms = self.payload(mid=f"msg-{i}")
            ms[0]["created_at_ms"] = 100000 + i
            self.arc.append_batch(cs, ms)
        self.assertEqual(len(self.arc.query(project_id="alpha", limit=100)), 100)
        self.assertEqual(len(json.loads(self.arc.export_conversation(
            project_id="alpha", conversation_id="chat-a"))["messages"]), 120)


if __name__ == "__main__":
    unittest.main()
