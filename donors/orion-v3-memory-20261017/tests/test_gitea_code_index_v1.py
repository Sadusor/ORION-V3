import tempfile
import unittest
from pathlib import Path
from orion_v3.modules.gitea_code_index_v1 import GiteaCodeIndex

A="a"*40
B="b"*40

class CodeIndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.index=GiteaCodeIndex(Path(self.tmp.name)/"code.sqlite3")
    def tearDown(self): self.tmp.cleanup()
    def seed(self,project="orion-v3",repo="MyGitea/ORION-V3",sha=A):
        return self.index.rebuild(project=project,repository=repo,commit_sha=sha,
            files=[{"path":"src/stop.py","text":"def stop_all():\n    stop_coordinator()\n","source_commit":sha},
                   {"path":"src/memory.py","text":"def retrieval():\n    search_memory_index()\n","source_commit":sha}])
    def test_retrieve_source_and_provenance(self):
        self.seed()
        hits=self.index.search("stop_coordinator",project="orion-v3",repository="MyGitea/ORION-V3",commit_sha=A)
        self.assertEqual(hits[0]["path"],"src/stop.py")
        self.assertEqual(hits[0]["trust"],"untrusted_source")
        self.assertEqual(hits[0]["source_commit"],A)
    def test_project_isolation(self):
        self.seed()
        with self.assertRaises(ValueError):
            self.index.search("stop",project="other",repository="MyGitea/ORION-V3",commit_sha=A)
    def test_stale_commit_denied(self):
        self.seed()
        with self.assertRaises(ValueError):
            self.index.search("stop",project="orion-v3",repository="MyGitea/ORION-V3",commit_sha=B)
    def test_rebuild_replaces_only_scope(self):
        self.seed()
        self.seed(project="other",repo="MyGitea/other")
        self.index.rebuild(project="orion-v3",repository="MyGitea/ORION-V3",commit_sha=B,
            files=[{"path":"x.py","text":"brand_new","source_commit":B}])
        self.assertTrue(self.index.search("brand_new",project="orion-v3",repository="MyGitea/ORION-V3",commit_sha=B))
        self.assertTrue(self.index.search("stop",project="other",repository="MyGitea/other",commit_sha=A))
    def test_mixed_commit_denied(self):
        with self.assertRaises(ValueError):
            self.index.rebuild(project="p",repository="x/y",commit_sha=A,
                files=[{"path":"x.py","text":"anything","source_commit":B}])
    def test_query_syntax_neutralized(self):
        self.seed()
        self.assertIsInstance(self.index.search('stop OR " AND *',project="orion-v3",repository="MyGitea/ORION-V3",commit_sha=A),list)
if __name__=="__main__":unittest.main()
