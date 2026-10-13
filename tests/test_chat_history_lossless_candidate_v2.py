"""Candidate-only regression tests. No production database paths or startup."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "orion_v3"))
from modules.chat_history_lossless_candidate_v2 import LosslessHistoryCandidate


def c(i, timestamp=None, deleted=0, title=None):
    ts = timestamp if timestamp is not None else 1000 + i
    return dict(id=f"c{i}", title=title or f"Chat {i}", project_id="orion-v3",
                pinned=0, archived=0, deleted=deleted,
                created_at_ms=1000 + i, updated_at_ms=ts)


class LosslessCandidateTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="orion-candidate-chat-")
        self.addCleanup(temp.cleanup)
        self.db = LosslessHistoryCandidate(Path(temp.name) / "only-test.sqlite3")

    def test_fifty_one_conversations_preserved_but_fifty_visible(self):
        self.db.sync({"conversations": [c(i) for i in range(51)]})
        self.assertEqual(len(self.db.snapshot()["conversations"]), 51)
        self.assertEqual(len(self.db.visible()), 50)

    def test_long_text_preserved(self):
        original = "α" * 12000
        self.db.sync({"conversations": [c(1)], "messages": [
            dict(id="m1", conversation_id="c1", role="assistant", text=original,
                 source="orion", created_at_ms=2000)]})
        self.assertEqual(self.db.snapshot()["messages"][0]["text"], original)

    def test_deleted_not_resurrected(self):
        self.db.sync({"conversations": [c(1, 5000, deleted=1)]})
        self.db.sync({"conversations": [c(1, 6000, deleted=0)]})
        self.assertEqual(self.db.snapshot()["conversations"][0]["deleted"], 1)
        self.assertEqual(len(self.db.visible()), 0)

    def test_equal_timestamp_first_wins(self):
        self.db.sync({"conversations": [c(1, 5000, title="first")]})
        self.db.sync({"conversations": [c(1, 5000, title="second")]})
        self.assertEqual(self.db.snapshot()["conversations"][0]["title"], "first")

    def test_messages_survive_restart_and_duplicates(self):
        payload = {"conversations": [c(1)], "messages": [
            dict(id="m1", conversation_id="c1", role="user", text="Hello",
                 source="pc", created_at_ms=2000)]}
        self.db.sync(payload)
        self.db.sync(payload)
        reopened = LosslessHistoryCandidate(self.db.path)
        self.assertEqual(len(reopened.snapshot()["messages"]), 1)

    def test_invalid_batch_atomic(self):
        with self.assertRaises(ValueError):
            self.db.sync({"conversations": [c(1)], "messages": [
                dict(id="bad", conversation_id="unknown", role="user",
                     text="hello", created_at_ms=2000)]})
        self.assertEqual(len(self.db.snapshot()["conversations"]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
