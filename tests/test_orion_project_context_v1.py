import unittest
from unittest.mock import patch
from orion_v3.modules.orion_project_context_v1 import (
    is_orion_project_question,project_status_context,render_project_status_context)
from orion_v3.modules.gitea_chat_brain_v1 import GiteaChatStreamingBrain,gitea_chat_request

SHA="a"*40
class ProjectContextTests(unittest.TestCase):
    def test_natural_project_question(self):
        self.assertTrue(is_orion_project_question("Qwen tell me what ORION V3 is and where we stand in our roadmap"))
        self.assertFalse(is_orion_project_question("What's the weather?"))
    def test_only_pinned_checkpoint(self):
        class Api:
            def branches(self,*a):return [{"name":"main","commit_id":SHA}]
        with self.assertRaises(ValueError):project_status_context(Api())
    def test_result_has_source_citation(self):
        obj={"repository":"MyGitea/ORION-V3","branch":"orion-checkpoint-20261010",
             "source_commit":SHA,"files":[{"path":"docs/ROADMAP.md","text":"progress"}]}
        prompt=render_project_status_context(obj)
        self.assertIn("docs/ROADMAP.md",prompt)
        self.assertIn(SHA,prompt)
    def test_normal_chat_is_unchanged(self):
        with patch("orion_v3.modules.gitea_chat_brain_v1.StreamingBrainPipeline.start",return_value={}) as start:
            GiteaChatStreamingBrain().start("hello")
            self.assertEqual(start.call_args.args[0],"hello")
    def test_orion_natural_chat_uses_checkpoint(self):
        context={"repository":"MyGitea/ORION-V3","branch":"orion-checkpoint-20261010",
                 "source_commit":SHA,"files":[{"path":"docs/ROADMAP.md","text":"verified evidence"}]}
        with patch("orion_v3.modules.gitea_chat_brain_v1.project_status_context",return_value=context),patch("orion_v3.modules.gitea_chat_brain_v1.StreamingBrainPipeline.start",return_value={}) as start:
            with gitea_chat_request(project_id="orion-v3",owner_text="what is ORION V3 roadmap?",state_dir="."):
                GiteaChatStreamingBrain().start("final frozen memory prompt")
            self.assertIn("verified evidence",start.call_args.args[0])
            self.assertIn("final frozen memory prompt",start.call_args.args[0])
if __name__=="__main__": unittest.main()
