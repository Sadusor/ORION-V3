"""Android Stage C atomic-delete source contracts; actual Kotlin compile is in GITCHECK."""
import unittest
from pathlib import Path

STORE = Path("android/app/src/main/java/com/sadusor/orionv3/history/ChatHistoryStore.kt")
BRIDGE = Path("android/app/src/main/java/com/sadusor/orionv3/online/OrionPcBridge.kt")


class AtomicAndroidTombstoneContract(unittest.TestCase):
    def test_schema_migration_preserves_existing_rows(self):
        text = STORE.read_text(encoding="utf-8")
        self.assertIn("private const val DB_VERSION = 2", text)
        self.assertIn("if (oldVersion < 2)", text)
        self.assertIn("deleted_archive_conversations", text)
        self.assertNotIn("DROP TABLE", text)

    def test_atomic_delete_and_permanent_replay_guard(self):
        text = STORE.read_text(encoding="utf-8")
        self.assertIn("fun applyArchiveTombstones", text)
        self.assertIn("db.beginTransaction()", text)
        self.assertIn('db.delete("messages", "conversation_id=?"', text)
        self.assertIn('db.delete("conversations", "id=?"', text)
        self.assertIn("tombstoned(db, conversationId)", text)
        self.assertIn("tombstoned(db, id)", text)
        self.assertIn("db.setTransactionSuccessful()", text)

    def test_bridge_consumes_authenticated_reconciliation(self):
        text = BRIDGE.read_text(encoding="utf-8")
        self.assertIn("ArchiveDeviceReconcileV1.removedIds(response)", text)
        self.assertIn("historyStore.applyArchiveTombstones(projectId, removed)", text)
        self.assertIn('prefs.getBoolean("archive_sync_opt_in", false)', text)
        self.assertIn('"/api/chat-history/sync"', text)


if __name__ == "__main__":
    unittest.main()
