import tempfile
import unittest
from pathlib import Path
from src.orion_v3.modules.gitea_multi_repo_chat_v1 import named_repo_scope, load_catalog

class MultiRepoChatTests(unittest.TestCase):
    def test_default_payday(self):
        with tempfile.TemporaryDirectory() as d:
            a=named_repo_scope("Show PayDay roadmap",state_dir=d)
            self.assertEqual(a["project"],"payday")
            self.assertEqual(a["repository"],"MyGitea/PayDay")
    def test_frozen_orion(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(named_repo_scope("ORION-V3 roadmap",state_dir=d))
    def test_inventory(self):
        with tempfile.TemporaryDirectory() as d:
            a=named_repo_scope("How many repositories in MyGitea2?",state_dir=d)
            self.assertEqual(a["kind"],"inventory")
    def test_count_followup_without_gitea_word(self):
        with tempfile.TemporaryDirectory() as d:
            a=named_repo_scope("how many repos we have in there?",state_dir=d)
            self.assertEqual(a["kind"],"inventory")
    def test_other_host_does_not_route(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(named_repo_scope("how many repos on GitHub?",state_dir=d))
    def test_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(named_repo_scope("Find unknown repo",state_dir=d))
    def test_catalog(self):
        with tempfile.TemporaryDirectory() as d:
            import json
            Path(d,"authorized-gitea-repositories.json").write_text(json.dumps({"repositories":[
                {"alias":"alpha","owner":"MyGitea","name":"Alpha","project":"alpha","authorized":True},
                {"alias":"beta","owner":"MyGitea","name":"Beta","project":"beta","authorized":True}]}))
            r=named_repo_scope("Read Beta docs",state_dir=d)
            self.assertEqual(r["project"],"beta")
            self.assertEqual(len(load_catalog(d)),2)
    def test_ambiguous(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(named_repo_scope("Compare PayDay and ORION-V3",state_dir=d)["kind"],"ambiguous")

if __name__=="__main__":
    unittest.main()
