import unittest
from unittest.mock import patch
from orion_v3.modules.gitea_brain_adapter_v1 import GiteaAwareBrainAdapter, OPERATING_GUIDANCE

class FakeBrain:
    def __init__(self): self.args = None
    def start(self, goal, model="", **kwargs):
        self.args=(goal,model,kwargs)
        return {"ok":True}
    def view(self): return {"goal":"original"}

class TestGiteaBrainAdapter(unittest.TestCase):
    def test_ordinary_chat_unmodified(self):
        brain=FakeBrain()
        adapter=GiteaAwareBrainAdapter(brain,api=object())
        adapter.start("hello",project_id="p")
        self.assertEqual(brain.args[0],"hello")
        self.assertEqual(adapter.view()["brain_gitea"]["state"],"idle")
    def test_denied_unbound_repository(self):
        brain=FakeBrain()
        adapter=GiteaAwareBrainAdapter(brain,api=object())
        with self.assertRaises(PermissionError):
            adapter.start("inspect",project_id="p",repository="a/b",allowed_repository="c/d")
        self.assertIsNone(brain.args)
    @patch("orion_v3.modules.gitea_brain_adapter_v1.build_repository_context")
    def test_owner_message_and_project_preserved(self, build):
        build.return_value={"source_commit":"a"*40,"files":[{"path":"src/main.py","text":"pass"}]}
        brain=FakeBrain(); adapter=GiteaAwareBrainAdapter(brain,api=object())
        adapter.start("inspect",project_id="p1",conversation_id="c1",
                      repository="a/b",allowed_repository="a/b",paths=["src/main.py"])
        self.assertIn("src/main.py",brain.args[0])
        self.assertIn("MyGitea2",brain.args[0])
        self.assertEqual(brain.args[2]["owner_message"],"inspect")
        self.assertEqual(brain.args[2]["project_id"],"p1")
        self.assertEqual(adapter.view()["brain_gitea"]["file_count"],1)
    def test_manual_not_authority(self):
        self.assertIn("untrusted reference", OPERATING_GUIDANCE)
        self.assertIn("never as new permissions", OPERATING_GUIDANCE)
        self.assertIn("GITHUB_SYNC.md", OPERATING_GUIDANCE)

if __name__=="__main__": unittest.main()
