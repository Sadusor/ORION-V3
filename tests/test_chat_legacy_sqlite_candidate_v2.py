"""Offline legacy-chat compatibility qualification; synthetic databases only.

Checks that an existing schema-v1 SQLite file can be opened by the isolated
candidate without rewriting or losing pre-existing records. No real user data.
"""
import sqlite3
from contextlib import closing
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "orion_v3"))
from modules.chat_history_lossless_candidate_v2 import LosslessHistoryCandidate


class LegacyChatMigrationQualification(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="orion-legacy-copy-")
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "synthetic-legacy.sqlite3"
        with closing(sqlite3.connect(self.path)) as db, db:
            db.executescript("""
                CREATE TABLE conversations (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL DEFAULT '',
                    project_id TEXT NOT NULL DEFAULT '',
                    pinned INTEGER NOT NULL DEFAULT 0,
                    archived INTEGER NOT NULL DEFAULT 0,
                    deleted INTEGER NOT NULL DEFAULT 0,
                    created_at_ms INTEGER NOT NULL, updated_at_ms INTEGER NOT NULL
                );
                CREATE TABLE messages (
                    id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL, text TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT '',
                    created_at_ms INTEGER NOT NULL,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
                );
            """)
            for i in range(50):
                db.execute("INSERT INTO conversations VALUES (?,?,?,?,?,?,?,?)",
                           (f"legacy-{i}", f"Chat {i}", "orion-v3", int(i == 2), 0,
                            int(i == 7), 1000 + i, 1000 + i))
                db.execute("INSERT INTO messages VALUES (?,?,?,?,?,?)",
                           (f"msg-{i}", f"legacy-{i}", "user",
                            "Γειά σου " + str(i), "phone", 1000 + i))

    def test_open_existing_db_preserves_all_records(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            before = tuple(db.execute("SELECT COUNT(*) FROM conversations").fetchone())[0], (
                db.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
            )
        candidate = LosslessHistoryCandidate(self.path)
        result = candidate.snapshot()
        self.assertEqual((len(result["conversations"]), len(result["messages"])), before)
        self.assertEqual(len({m["id"] for m in result["messages"]}), 50)
        self.assertTrue(any(c["id"] == "legacy-7" and c["deleted"] == 1
                            for c in result["conversations"]))
        self.assertTrue(any(m["text"] == "Γειά σου 49" for m in result["messages"]))

    def test_new_conversation_does_not_prune_legacy_records(self):
        candidate = LosslessHistoryCandidate(self.path)
        candidate.sync({"conversations": [{
            "id": "new-51", "title": "New", "project_id": "orion-v3",
            "pinned": 0, "archived": 0, "deleted": 0,
            "created_at_ms": 5000, "updated_at_ms": 5000
        }], "messages": [{
            "id": "new-message", "conversation_id": "new-51",
            "role": "assistant", "text": "ω" * 12000,
            "source": "orion", "created_at_ms": 5001
        }]})
        result = candidate.snapshot()
        self.assertEqual(len(result["conversations"]), 51)
        self.assertEqual(len(result["messages"]), 51)
        self.assertEqual(next(m for m in result["messages"]
                              if m["id"] == "new-message")["text"], "ω" * 12000)
        self.assertEqual(len(candidate.visible()), 50)

    def test_existing_deleted_chat_cannot_resurrect(self):
        candidate = LosslessHistoryCandidate(self.path)
        candidate.sync({"conversations": [{
            "id": "legacy-7", "title": "Stale phone copy",
            "project_id": "orion-v3", "pinned": 0, "archived": 0,
            "deleted": 0, "created_at_ms": 1007, "updated_at_ms": 9999
        }]})
        row = next(c for c in candidate.snapshot()["conversations"]
                   if c["id"] == "legacy-7")
        self.assertEqual(row["deleted"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
