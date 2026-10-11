import tempfile
from contextlib import closing
import unittest
from pathlib import Path
from src.orion_v3.modules.history_archive_v1 import HistoryArchiveV1
from src.orion_v3.modules.history_archive_search_projection_v1 import ArchiveSearchProjectionV1

class ArchiveProjectionTests(unittest.TestCase):
    def test_project_scope_and_owner_delete_refresh(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            archive=HistoryArchiveV1(root/"source.sqlite3")
            archive.append_batch([
                {"id":"c1","project_id":"one"},
                {"id":"c2","project_id":"two"}],
                [{"id":"m1","conversation_id":"c1","created_at_ms":1,"role":"user","text":"unique heliosphere"},
                 {"id":"m2","conversation_id":"c2","created_at_ms":2,"role":"user","text":"unique heliosphere"}])
            projection=ArchiveSearchProjectionV1(root/"source.sqlite3",root/"projection.sqlite3")
            self.assertEqual(projection.refresh(),2)
            self.assertEqual([r["conversation_id"] for r in projection.search(project_id="one",query="heliosphere")],["c1"])
            self.assertEqual([r["conversation_id"] for r in projection.search(project_id="two",query="heliosphere")],["c2"])
            with self.assertRaises(ValueError):
                projection.search(project_id="",query="heliosphere")
            import sqlite3
            with closing(sqlite3.connect(root/"source.sqlite3")) as db:
                db.execute("UPDATE conversations SET deleted_at_ms=10 WHERE id='c1'")
                db.commit()
            projection.refresh()
            self.assertEqual(projection.search(project_id="one",query="heliosphere"),[])
            self.assertEqual(len(projection.search(project_id="two",query="heliosphere")),1)
            with sqlite3.connect(root/"source.sqlite3") as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM messages").fetchone()[0],2)

if __name__=="__main__":
    unittest.main()
