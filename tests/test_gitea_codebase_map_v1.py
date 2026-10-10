import unittest
from orion_v3.modules.gitea_codebase_map_v1 import create_codebase_map

SHA = "a" * 40
class CodebaseMapTests(unittest.TestCase):
    def test_source_only_and_provenance(self):
        tree={"sha":"b"*40,"truncated":False,"tree":[
            {"type":"blob","path":"src/main.py","sha":"1"*40},
            {"type":"blob","path":"docs/README.md","sha":"2"*40},
            {"type":"blob","path":".env","sha":"3"*40},
            {"type":"blob","path":"node_modules/fake.py","sha":"4"*40},
            {"type":"blob","path":"../../private.py","sha":"5"*40},
            {"type":"blob","path":"token.pem","sha":"6"*40}]}
        out=create_codebase_map(tree,owner="owner",repository="repo",commit_sha=SHA)
        self.assertEqual(out["file_count"],2)
        self.assertEqual(out["source_commit"],SHA)
        self.assertEqual(out["authority"],"context_only")
        self.assertEqual([x["path"] for x in out["files"]],["docs/README.md","src/main.py"])
    def test_truncated_fails_closed(self):
        with self.assertRaises(ValueError):
            create_codebase_map({"truncated":True,"tree":[]},owner="o",repository="r",commit_sha=SHA)
    def test_invalid_ref_fails_closed(self):
        with self.assertRaises(ValueError):
            create_codebase_map({"tree":[]},owner="o",repository="r",commit_sha="main")
    def test_large_tree_fails_closed(self):
        with self.assertRaises(ValueError):
            create_codebase_map({"tree":[{}]*5001},owner="o",repository="r",commit_sha=SHA)
if __name__ == "__main__":
    unittest.main()
