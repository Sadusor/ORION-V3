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
    def test_oversized_roadmap_skipped_with_checkpoint_preserved(self):
        from unittest.mock import patch
        class Api:
            def branches(self,*args):
                return [{"name":"orion-checkpoint-20261010","commit_id":SHA}]
            def tree(self,*args):return {"truncated":False,"tree":[]}
        mapped={"files":[{"path":"docs/checkpoints/ORION_V3_GITEA_HANDOFF_2026-10-10.md"},
                         {"path":"docs/ROADMAP.md"}]}
        def read(api,owner,repo,sha,path):
            if path.endswith("ROADMAP.md"):
                raise ValueError("Unsupported or oversized file")
            return {"text":"verified handoff"}
        with patch("orion_v3.modules.orion_project_context_v1.create_codebase_map",return_value=mapped),patch("orion_v3.modules.orion_project_context_v1.get_source_context",side_effect=read):
            result=project_status_context(Api())
        self.assertEqual(len(result["files"]),1)
        self.assertIn("verified handoff",result["files"][0]["text"])
    def test_large_retrieved_context_fits_brain_request(self):
        from orion_v3.modules.gitea_chat_brain_v1 import attach_bounded_reference
        owner_prompt="owner request " + ("memory " * 900)
        result=attach_bounded_reference(owner_prompt,"document " * 3000)
        self.assertTrue(result.startswith(owner_prompt))
        self.assertLessEqual(len(result.encode("utf-8")),15900)
    def test_greek_context_byte_budget(self):
        from orion_v3.modules.gitea_chat_brain_v1 import attach_bounded_reference
        result=attach_bounded_reference("ελληνικά","πληροφορίες " * 3000)
        self.assertLessEqual(len(result.encode("utf-8")),15900)
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
