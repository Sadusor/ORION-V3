"""Focused regression for existing ORION chat store. All databases disposable."""
import sqlite3
from contextlib import closing
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"/"orion_v3"))
from modules.chat_history import ChatHistoryStore

def conv(i, deleted=0, ts=None):
    n=1000+i if ts is None else ts
    return {"id":f"c{i}", "title":f"Chat {i}", "project_id":"orion-v3",
            "pinned":0,"archived":0,"deleted":deleted,
            "created_at_ms":1000+i,"updated_at_ms":n}

class ExistingChatSafety(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="orion-existing-chat-")
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/"test.sqlite3"
        self.store=ChatHistoryStore(self.path)

    def test_retention_is_not_destruction(self):
        self.store.sync({"conversations":[conv(i) for i in range(65)]})
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("select count(*) from conversations").fetchone()[0],65)

    def test_long_message_saved_exactly(self):
        original="Γ"*12000
        self.store.sync({"conversations":[conv(1)],"messages":[{
            "id":"long1","conversation_id":"c1","role":"assistant",
            "text":original,"source":"orion","created_at_ms":2000}]})
        with closing(sqlite3.connect(self.path)) as db:
            actual=db.execute("select text from messages where id='long1'").fetchone()[0]
        self.assertEqual(actual,original)

    def test_orphan_never_creates_chat(self):
        self.store.sync({"messages":[{
            "id":"orphan","conversation_id":"missing","role":"user",
            "text":"hello","source":"phone","created_at_ms":2000}]})
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("select count(*) from conversations").fetchone()[0],0)

    def test_deleted_bit_not_cleared_by_newer_metadata(self):
        self.store.sync({"conversations":[conv(1,deleted=1,ts=2000)]})
        self.store.sync({"conversations":[conv(1,deleted=0,ts=3000)]})
        with closing(sqlite3.connect(self.path)) as db:
            deleted=db.execute("select deleted from conversations where id='c1'").fetchone()[0]
        self.assertEqual(deleted,1)

    def test_android_no_destructive_prune_or_truncation(self):
        src=(ROOT/"android/app/src/main/java/com/sadusor/orionv3/history/ChatHistoryStore.kt").read_text(encoding="utf-8")
        self.assertNotIn("prune(db)",src)
        self.assertNotIn('clean(raw.optString("text"), MAX_TEXT_CHARS)',src)
        self.assertIn('val text = raw.optString("text").trim()',src)

if __name__=="__main__":
    unittest.main(verbosity=2)
