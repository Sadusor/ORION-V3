"""Read-only-to-production chat integrity probes. Uses only disposable temp SQLite stores.

These tests prove whether the *source implementation* exhibits DeepSeek's
reported failure modes. A PASS means the defect is reproducible, NOT repaired.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "orion_v3"))
from modules.chat_history import ChatHistoryStore


def conv(cid: str, ts: int, deleted: int = 0, title: str = "chat") -> dict:
    return {
        "id": cid, "title": title, "project_id": "orion-v3",
        "pinned": 0, "archived": 0, "deleted": deleted,
        "created_at_ms": ts, "updated_at_ms": ts,
    }


def msg(mid: str, cid: str, text: str, ts: int) -> dict:
    return {
        "id": mid, "conversation_id": cid, "role": "assistant",
        "text": text, "source": "orion-probe", "created_at_ms": ts,
    }


class ChatIntegrityReproduction(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="orion-chat-disposable-")
        self.addCleanup(self.tmp.cleanup)
        self.store = ChatHistoryStore(Path(self.tmp.name) / "test-only.sqlite3")

    def test_reproduces_hard_delete_at_51_conversations(self):
        self.store.sync({"conversations": [conv(f"c{i:03d}", 1000 + i) for i in range(51)]})
        result = self.store.snapshot()
        self.assertEqual(len(result["conversations"]), 50)
        self.assertNotIn("c000", {c["id"] for c in result["conversations"]})
        print("REPRO_C3> CONFIRMED: 51 input conversations -> 50 retained; oldest deleted")

    def test_reproduces_message_truncation_at_8000_chars(self):
        original = "x" * 12000
        result = self.store.sync({
            "conversations": [conv("long", 1000)],
            "messages": [msg("long-msg", "long", original, 1001)],
        })
        saved = next(m["text"] for m in result["messages"] if m["id"] == "long-msg")
        self.assertEqual(len(saved), 8000)
        print("REPRO_C5> CONFIRMED: 12000 input characters -> 8000 stored")

    def test_reproduces_deleted_conversation_resurrection(self):
        self.store.sync({"conversations": [conv("gone", 5000, deleted=1)]})
        result = self.store.sync({"conversations": [conv("gone", 6000, deleted=0)]})
        row = next(c for c in result["conversations"] if c["id"] == "gone")
        self.assertEqual(row["deleted"], 0)
        print("REPRO_C4> CONFIRMED: newer undeleted metadata resurrects deleted chat")

    def test_reproduces_equal_timestamp_overwrite(self):
        self.store.sync({"conversations": [conv("tie", 5000, title="first")]})
        result = self.store.sync({"conversations": [conv("tie", 5000, title="second")]})
        row = next(c for c in result["conversations"] if c["id"] == "tie")
        self.assertEqual(row["title"], "second")
        print("REPRO_C11> CONFIRMED: Python accepts equal-timestamp overwrite")


if __name__ == "__main__":
    unittest.main(verbosity=2)
