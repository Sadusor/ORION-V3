import unittest
from unittest.mock import patch
from pathlib import Path
from orion_v3.modules.gitea_chat_brain_v1 import GiteaChatStreamingBrain, gitea_chat_request

SEARCH = "orion_v3.modules.gitea_chat_brain_v1.search_live_gitea_v2"
START = "orion_v3.modules.gitea_chat_brain_v1.StreamingBrainPipeline.start"


class ChatBridgeTests(unittest.TestCase):
    def test_ordinary_chat_unchanged(self):
        with patch(START, return_value={"ok": True}) as start:
            GiteaChatStreamingBrain().start("hello", "qwen")
            self.assertEqual(start.call_args.args, ("hello", "qwen"))

    def test_live_v2_search_injects_cited_source_after_memory(self):
        commit = "a" * 40
        context = {
            "repository": "MyGitea/ORION-V3", "source_commit": commit,
            "results": [{"path": "src/stop.py", "part": 0, "text": "def stop(): pass"}],
            "authority": "context_only", "may_write": False,
        }
        with patch(SEARCH, return_value=context) as search, patch(START, return_value={"ok": True}) as start:
            with gitea_chat_request(project_id="orion-v3", owner_text="where is stop?", state_dir=Path(".")):
                GiteaChatStreamingBrain().start("frozen memory final prompt", "qwen")
            self.assertEqual(search.call_count, 1)
            self.assertEqual(search.call_args.kwargs["project_id"], "orion-v3")
            self.assertEqual(search.call_args.kwargs["query"], "stop")
            composed = start.call_args.args[0]
            self.assertIn("frozen memory final prompt", composed)
            self.assertIn("src/stop.py", composed)
            self.assertIn(commit, composed)
            self.assertIn("authority='context_only'", composed)

    def test_other_project_cannot_search(self):
        with patch(SEARCH) as search, patch(START, return_value={}) as start:
            with gitea_chat_request(project_id="other", owner_text="search", state_dir=Path(".")):
                GiteaChatStreamingBrain().start("hello")
            search.assert_not_called()
            self.assertEqual(start.call_args.args[0], "hello")

    def test_v2_lookup_failure_disclosed_without_fake_evidence(self):
        with patch(SEARCH, side_effect=ValueError("unavailable")), patch(START, return_value={}) as start:
            with gitea_chat_request(project_id="orion-v3", owner_text="find code", state_dir=Path(".")):
                GiteaChatStreamingBrain().start("owner")
            composed = start.call_args.args[0]
            self.assertIn("indexed search failed", composed)
            self.assertNotIn("<ORION_INDEXED_SOURCES", composed)


if __name__ == "__main__":
    unittest.main()
