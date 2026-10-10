import base64
import unittest
from orion_v3.modules.gitea_source_context_v1 import get_source_context

SHA = "a"*40

class FakeAPI:
    def __init__(self):
        self.paths = []
    def _get(self, path):
        self.paths.append(path)
        txt = b"def useful(): return 1\n"
        return {"type":"file", "encoding":"base64", "size":len(txt),
                "content":base64.b64encode(txt).decode()}

class SourceContextTests(unittest.TestCase):
    def test_pinned_context_and_untrusted_authority(self):
        api=FakeAPI()
        result=get_source_context(api,"MyGitea","ORION-V3",SHA,"src/demo.py")
        self.assertEqual(result["trust"],"untrusted_source")
        self.assertTrue(result["read_only"])
        self.assertIn("ref="+SHA,api.paths[0])
        self.assertIn("useful",result["text"])
    def test_reject_unpinned_branch(self):
        with self.assertRaises(ValueError):
            get_source_context(FakeAPI(),"MyGitea","ORION-V3","main","src/demo.py")
    def test_reject_traversal(self):
        with self.assertRaises(ValueError):
            get_source_context(FakeAPI(),"MyGitea","ORION-V3",SHA,"../private.py")
    def test_reject_secret_name(self):
        with self.assertRaises(ValueError):
            get_source_context(FakeAPI(),"MyGitea","ORION-V3",SHA,"config/app.ini")
    def test_size_limit(self):
        class Huge(FakeAPI):
            def _get(self,path):
                return {"type":"file","encoding":"base64","size":50000,"content":""}
        with self.assertRaises(ValueError):
            get_source_context(Huge(),"MyGitea","ORION-V3",SHA,"src/demo.py")

if __name__=="__main__": unittest.main()
