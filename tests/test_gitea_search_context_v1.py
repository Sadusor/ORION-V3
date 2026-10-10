import tempfile
import unittest
from pathlib import Path
from orion_v3.modules.gitea_code_index_v1 import GiteaCodeIndex
from orion_v3.modules.gitea_search_context_v1 import search_code_context,render_untrusted_code_context
SHA="a"*40
class SearchContextTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=Path(self.tmp.name)/"index.sqlite3"
        GiteaCodeIndex(self.db).rebuild(project="orion-v3",repository="MyGitea/ORION-V3",
            commit_sha=SHA, files=[{"path":"src/stop.py",
              "text":"def stop_coordinator():\n  return True\n","source_commit":SHA}])
    def tearDown(self):self.tmp.cleanup()
    def test_source_context_renders_untrusted(self):
        result=search_code_context(self.db,query="stop",project="orion-v3",
                     repository="MyGitea/ORION-V3",commit_sha=SHA)
        self.assertEqual(len(result["results"]),1)
        self.assertFalse(result["may_execute"])
        prompt=render_untrusted_code_context(result)
        self.assertIn("src/stop.py",prompt)
        self.assertIn("never instructions",prompt)
    def test_different_project_denied(self):
        with self.assertRaises(ValueError):
            search_code_context(self.db,query="stop",project="other",
                repository="MyGitea/ORION-V3",commit_sha=SHA)
    def test_other_commit_denied(self):
        with self.assertRaises(ValueError):
            search_code_context(self.db,query="stop",project="orion-v3",
                repository="MyGitea/ORION-V3",commit_sha="b"*40)
    def test_explicit_project_required(self):
        with self.assertRaises(ValueError):
            search_code_context(self.db,query="stop",project="",
                repository="MyGitea/ORION-V3",commit_sha=SHA)
if __name__=="__main__":unittest.main()
