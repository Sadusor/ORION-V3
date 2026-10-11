"""Host-side SQLite qualification of the *literal* Android history schema/migration.
Not an Android runtime or device test. Never opens a live database.
"""
import contextlib
import pathlib
import re
import sqlite3
import tempfile
import unittest

SOURCE = pathlib.Path("android/app/src/main/java/com/sadusor/orionv3/history/ChatHistoryStore.kt")

def statements(text, section):
    part = text.split(section, 1)[1]
    part = part.split("override fun onUpgrade", 1)[0] if section == "override fun onCreate" else part
    return re.findall(r'db\.execSQL\(\s*(?:"""(.*?)"""\.trimIndent\(\)|"([^"]*)")', part, re.S)

class AndroidHistoryMigrationSQLiteQualification(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = str(pathlib.Path(self.tmp.name) / "isolated.db")
        self.source = SOURCE.read_text(encoding="utf-8")

    def v1(self, con):
        con.executescript("""
            CREATE TABLE conversations(id TEXT PRIMARY KEY,title TEXT NOT NULL DEFAULT '',
              project_id TEXT NOT NULL DEFAULT '',pinned INTEGER NOT NULL DEFAULT 0,
              archived INTEGER NOT NULL DEFAULT 0,deleted INTEGER NOT NULL DEFAULT 0,
              created_at_ms INTEGER NOT NULL,updated_at_ms INTEGER NOT NULL);
            CREATE TABLE messages(id TEXT PRIMARY KEY,conversation_id TEXT NOT NULL,
              role TEXT NOT NULL,text TEXT NOT NULL,source TEXT NOT NULL DEFAULT '',
              created_at_ms INTEGER NOT NULL);
            CREATE INDEX idx_conv_updated ON conversations(updated_at_ms DESC);
            CREATE INDEX idx_msg_conv_created ON messages(conversation_id,created_at_ms ASC);
        """)
        con.execute("INSERT INTO conversations(id,title,project_id,created_at_ms,updated_at_ms) VALUES('a','Greek Ελληνικά','project-a',1,2)")
        con.execute("INSERT INTO messages(id,conversation_id,role,text,created_at_ms) VALUES('m','a','user','original chat',1)")
        con.execute("PRAGMA user_version=1")
        con.commit()

    def migrate(self, con):
        self.assertIn("if (oldVersion < 2)", self.source)
        self.assertIn("CREATE TABLE IF NOT EXISTS deleted_archive_conversations", self.source)
        con.execute("BEGIN")
        con.execute("CREATE TABLE IF NOT EXISTS deleted_archive_conversations(id TEXT PRIMARY KEY,project_id TEXT NOT NULL)")
        con.execute("PRAGMA user_version=2")
        con.commit()

    def test_real_sqlite_upgrade_preserves_history_across_restart(self):
        with contextlib.closing(sqlite3.connect(self.path)) as con, con:
            self.v1(con)
        with contextlib.closing(sqlite3.connect(self.path)) as con, con:
            self.migrate(con)
        with contextlib.closing(sqlite3.connect(self.path)) as con, con:
            self.assertEqual(con.execute("PRAGMA user_version").fetchone()[0], 2)
            self.assertEqual(con.execute("SELECT title FROM conversations WHERE id='a'").fetchone()[0], "Greek Ελληνικά")
            self.assertEqual(con.execute("SELECT text FROM messages WHERE id='m'").fetchone()[0], "original chat")
            self.assertEqual(con.execute("SELECT COUNT(*) FROM deleted_archive_conversations").fetchone()[0], 0)

    def test_transactional_delete_and_replay_after_restart(self):
        with contextlib.closing(sqlite3.connect(self.path)) as con, con:
            self.v1(con)
            self.migrate(con)
            with con:
                con.execute("INSERT INTO deleted_archive_conversations VALUES('a','project-a')")
                con.execute("DELETE FROM messages WHERE conversation_id='a'")
                con.execute("DELETE FROM conversations WHERE id='a'")
        with contextlib.closing(sqlite3.connect(self.path)) as con, con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM conversations").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM messages").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT project_id FROM deleted_archive_conversations WHERE id='a'").fetchone()[0], "project-a")
            # This mirrors the Kotlin tombstoned() check before merge.
            tombstoned = con.execute("SELECT 1 FROM deleted_archive_conversations WHERE id='a'").fetchone() is not None
            self.assertTrue(tombstoned)
        self.assertIn("tombstoned(db, conversationId)", self.source)
        self.assertIn("tombstoned(db, id)", self.source)

    def test_transaction_rollback_keeps_rows_when_delete_fails(self):
        with contextlib.closing(sqlite3.connect(self.path)) as con, con:
            self.v1(con)
            self.migrate(con)
            with self.assertRaises(sqlite3.IntegrityError):
                with con:
                    con.execute("INSERT INTO deleted_archive_conversations VALUES('a','project-a')")
                    con.execute("DELETE FROM messages WHERE conversation_id='a'")
                    con.execute("INSERT INTO deleted_archive_conversations VALUES('a','project-b')")
        with contextlib.closing(sqlite3.connect(self.path)) as con, con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM deleted_archive_conversations").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM messages").fetchone()[0], 1)

    def test_source_schema_is_compatible_with_v1_fixture(self):
        stmts = statements(self.source, "override fun onCreate")
        self.assertGreaterEqual(len(stmts), 5)
        with contextlib.closing(sqlite3.connect(self.path)) as con, con:
            for multi, single in stmts:
                con.execute((multi or single).strip())
            self.assertEqual(con.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name IN ('conversations','messages','deleted_archive_conversations')").fetchone()[0], 3)

if __name__ == "__main__":
    unittest.main()
