"""Offline regression for read-only symbol evidence enrichment."""
import sqlite3
from contextlib import closing
import tempfile
import unittest
from pathlib import Path

from orion_v3.modules.gitea_symbol_evidence_v1 import enrich_symbol_evidence


class SymbolEvidenceTests(unittest.TestCase):
    def test_sync_button_source_and_neighbor_are_selected(self):
        commit = "a" * 40
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "index.sqlite3"
            with closing(sqlite3.connect(path)) as db:
                db.execute("CREATE TABLE code_revision(project TEXT,repository TEXT,commit_sha TEXT)")
                db.execute("CREATE TABLE code_fts(project TEXT,repository TEXT,commit_sha TEXT,path TEXT,part TEXT,text TEXT)")
                db.execute("INSERT INTO code_revision VALUES(?,?,?)", ("orion-v3", "MyGitea/ORION-V3", commit))
                db.executemany("INSERT INTO code_fts VALUES(?,?,?,?,?,?)", [
                    ("orion-v3","MyGitea/ORION-V3",commit,"ui/strata/modules/chat-history.js","0",
                     "function syncNow() { return bridge.call('/api/chat-history/sync'); }"),
                    ("orion-v3","MyGitea/ORION-V3",commit,"ui/strata/modules/chat-history.js","7",
                     "<button id='orionHistoryRefresh' title='Refresh history'>"),
                    ("orion-v3","MyGitea/ORION-V3",commit,"ui/strata/modules/chat-history.js","9",
                     "<button id='orionHistoryDesktopRefresh' title='Refresh history'>"),
                    ("orion-v3","MyGitea/ORION-V3",commit,"docs/sync.md","0",
                     "Historical notes about sync"),
                ])
                db.commit()
            result = enrich_symbol_evidence(path, {"results": []},
                query="Which file implements the sync button in MyGitea2?",
                project="orion-v3", repository="MyGitea/ORION-V3",
                commit_sha=commit, max_chars=6000)
            paths = [r["path"] for r in result["results"]]
            self.assertEqual(paths[0], "ui/strata/modules/chat-history.js")
            evidence = " ".join(r["text"] for r in result["results"])
            for expected in ("orionHistoryRefresh", "orionHistoryDesktopRefresh", "syncNow", "/api/chat-history/sync"):
                self.assertIn(expected, evidence)
            self.assertTrue(all(r["source_commit"] == commit for r in result["results"]))

    def test_stale_commit_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "index.sqlite3"
            with closing(sqlite3.connect(path)) as db:
                db.execute("CREATE TABLE code_revision(project TEXT,repository TEXT,commit_sha TEXT)")
                db.execute("CREATE TABLE code_fts(project TEXT,repository TEXT,commit_sha TEXT,path TEXT,part TEXT,text TEXT)")
                db.execute("INSERT INTO code_revision VALUES('orion-v3','MyGitea/ORION-V3',?)", ("a"*40,))
                db.commit()
            with self.assertRaises(ValueError):
                enrich_symbol_evidence(path, {"results":[]}, query="find sync button",
                    project="orion-v3",repository="MyGitea/ORION-V3",
                    commit_sha="b"*40)


if __name__ == "__main__":
    unittest.main()
