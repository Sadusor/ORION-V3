import unittest
from unittest.mock import patch
from pathlib import Path
from orion_v3.modules.gitea_chat_brain_v1 import GiteaChatStreamingBrain,gitea_chat_request

class ChatBridgeTests(unittest.TestCase):
    def test_ordinary_chat_unchanged(self):
        with patch("orion_v3.modules.gitea_chat_brain_v1.StreamingBrainPipeline.start",return_value={"ok":True}) as start:
            GiteaChatStreamingBrain().start("hello","qwen")
            self.assertEqual(start.call_args.args,("hello","qwen"))
    def test_opt_in_injects_after_memory(self):
        context={"repository":"MyGitea/ORION-V3","source_commit":"a"*40,
                 "results":[{"path":"src/stop.py","part":0,"source_commit":"a"*40,"text":"def stop(): pass"}],
                 "authority":"context_only","may_write":False}
        with patch("orion_v3.modules.gitea_chat_brain_v1.search_live_gitea",return_value=context),patch("orion_v3.modules.gitea_chat_brain_v1.StreamingBrainPipeline.start",return_value={"ok":True}) as start:
            with gitea_chat_request(project_id="orion-v3",owner_text="where is stop?",state_dir=Path(".")):
                GiteaChatStreamingBrain().start("frozen memory final prompt","qwen")
            self.assertIn("frozen memory final prompt",start.call_args.args[0])
            self.assertIn("src/stop.py",start.call_args.args[0])
            self.assertIn("No writes",start.call_args.args[0])
    def test_other_project_cannot_search(self):
        with patch("orion_v3.modules.gitea_chat_brain_v1.search_live_gitea") as search,patch("orion_v3.modules.gitea_chat_brain_v1.StreamingBrainPipeline.start",return_value={}) as start:
            with gitea_chat_request(project_id="other",owner_text="search",state_dir=Path(".")):
                GiteaChatStreamingBrain().start("hello")
            search.assert_not_called()
            self.assertEqual(start.call_args.args[0],"hello")
    def test_lookup_failure_is_disclosed(self):
        with patch("orion_v3.modules.gitea_chat_brain_v1.search_live_gitea",side_effect=ValueError("unavailable")),patch("orion_v3.modules.gitea_chat_brain_v1.StreamingBrainPipeline.start",return_value={}) as start:
            with gitea_chat_request(project_id="orion-v3",owner_text="find code",state_dir=Path(".")):
                GiteaChatStreamingBrain().start("owner")
            self.assertIn("search unavailable",start.call_args.args[0])
if __name__=="__main__":unittest.main()
