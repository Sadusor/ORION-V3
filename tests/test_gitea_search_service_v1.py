import tempfile
import unittest
from pathlib import Path
from orion_v3.modules.gitea_search_service_v1 import search_live_gitea
SHA="a"*40
class FakeGitea:
    def repository(self,*a):return {"default_branch":"main"}
    def branches(self,*a):return [{"name":"main","commit_id":SHA}]
    def tree(self,*a):
        return {"sha":"b"*40,"truncated":False,
                "tree":[{"type":"blob","path":"src/stop.py","sha":"c"*40}]}
    def _get(self,uri):
        import base64
        content=b"def stop_coordinator():\n    return True\n"
        return {"type":"file","size":len(content),"encoding":"base64",
                "content":base64.b64encode(content).decode()}
class ServiceTests(unittest.TestCase):
    def test_live_project_search(self):
        with tempfile.TemporaryDirectory() as folder:
            result=search_live_gitea(query="stop",project_id="orion-v3",state_dir=folder,api=FakeGitea())
            self.assertEqual(result["indexed_files"],1)
            self.assertEqual(result["results"][0]["path"],"src/stop.py")
            self.assertEqual(result["source_commit"],SHA)
            self.assertFalse(result["may_write"])
    def test_project_denied(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(PermissionError):
                search_live_gitea(query="stop",project_id="other",state_dir=folder,api=FakeGitea())
    def test_directory_not_autocreated(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                search_live_gitea(query="stop",project_id="orion-v3",
                    state_dir=Path(folder)/"not-created",api=FakeGitea())
if __name__=="__main__":unittest.main()
