import unittest
import tempfile
import sqlite3
from pathlib import Path
from contextlib import closing
from src.orion_v3.modules.history_archive_v1 import HistoryArchiveV1
from src.orion_v3.modules.history_archive_index_sync_v1 import ArchiveIndexSyncV1

class ArchiveIndexSyncTests(unittest.TestCase):
    def test_committed_history_indexed_then_deleted(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            archive=HistoryArchiveV1(root/"archive.sqlite3")
            adapter=ArchiveIndexSyncV1(root/"archive.sqlite3",root/"search.sqlite3")
            archive.append_batch(
                [{"id":"conversation-one","project_id":"project-one"}],
                [{"id":"message-one","conversation_id":"conversation-one",
                  "role":"user","text":"nebula archive marker",
                  "created_at_ms":100}])
            self.assertEqual(adapter.after_archive_commit()["indexed_messages"],1)
            self.assertEqual(len(adapter.retrieve(project_id="project-one",query="nebula")),1)
            self.assertEqual(adapter.retrieve(project_id="project-two",query="nebula"),[])
            with closing(sqlite3.connect(root/"archive.sqlite3")) as db:
                db.execute("UPDATE conversations SET deleted_at_ms=200 WHERE id=?",
                           ("conversation-one",))
                db.commit()
            self.assertEqual(adapter.after_owner_deletion()["indexed_messages"],0)
            self.assertEqual(adapter.retrieve(project_id="project-one",query="nebula"),[])
            with closing(sqlite3.connect(root/"archive.sqlite3")) as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM messages").fetchone()[0],1)

if __name__=="__main__":
    unittest.main()
