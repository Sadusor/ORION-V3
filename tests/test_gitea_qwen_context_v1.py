import unittest
from unittest.mock import patch
from orion_v3.modules.gitea_qwen_context_v1 import build_repository_context

SHA = "a"*40
class API:
    def repository(self,*args): return {"default_branch":"main"}
    def branches(self,*args): return [{"name":"main","commit_id":SHA}]
    def tree(self,*args): return {"sha":"b"*40,"truncated":False,
        "tree":[{"type":"blob","path":"src/main.py","sha":"c"*40}]}

class ContextTests(unittest.TestCase):
    @patch("orion_v3.modules.gitea_qwen_context_v1.get_source_context")
    def test_scope_and_bound_context(self, fetch):
        fetch.return_value={"text":"print('ok')"}
        r=build_repository_context(API(),owner="MyGitea",repo="ORION-V3",
            allowed_repository="MyGitea/ORION-V3", paths=["src/main.py"])
        self.assertEqual(r["source_commit"],SHA)
        self.assertEqual(len(r["files"]),1)
        self.assertFalse(r["may_write"])
        self.assertEqual(r["authority"],"context_only")
    def test_cross_project_fails(self):
        with self.assertRaises(PermissionError):
            build_repository_context(API(),owner="Other",repo="ORION-V3",
                allowed_repository="MyGitea/ORION-V3",paths=[])
    def test_unmapped_path_fails(self):
        with self.assertRaises(ValueError):
            build_repository_context(API(),owner="MyGitea",repo="ORION-V3",
                allowed_repository="MyGitea/ORION-V3",paths=["secret.txt"])
    def test_budget_fails(self):
        with self.assertRaises(ValueError):
            build_repository_context(API(),owner="MyGitea",repo="ORION-V3",
                allowed_repository="MyGitea/ORION-V3",paths=[],max_total_chars=999999)
if __name__=="__main__":unittest.main()
