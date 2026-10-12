import unittest
from src.orion_v3.modules.orion_understanding_v1 import interpret, rank_source_path, rank_unique_paths


class UnderstandingV1Tests(unittest.TestCase):
    def test_natural_language_controls(self):
        result = interpret("Where did we build the controls in MyGitea2?")
        self.assertIn("button", result.search_query.split())
        self.assertIn("ui", result.search_query.split())
        self.assertEqual(result.intent, "source_lookup")

    def test_preserves_original(self):
        question = "Show me the buttons we added yesterday"
        self.assertEqual(interpret(question).owner_request, question)

    def test_implementation_above_test(self):
        concepts = interpret("Where is the UI button code?").concepts
        implementation = rank_source_path("ui/strata/modules/chat-history.js", concepts=concepts)
        test = rank_source_path("tests/test_chat_history.py", concepts=concepts)
        self.assertGreater(implementation, test)

    def test_deduplicated_ui_ranking(self):
        concepts = interpret("Where did we build the UI controls?").concepts
        paths = (["android/app/src/main/java/com/sadusor/orionv3/history/ChatHistoryStore.kt"] * 12
                 + ["ui/strata/modules/chat-reading-controls-v1.js",
                    "ui/strata/modules/conversation-controls-v2.js",
                    "tests/test_ui_controls.py"])
        ranked = rank_unique_paths(paths, concepts=concepts)
        self.assertEqual(len(ranked), len(set(ranked)))
        self.assertTrue(ranked[0].startswith("ui/"))
        self.assertTrue(ranked[1].startswith("ui/"))

    def test_no_authorization_grant(self):
        result = interpret("Find controls in my private repositories")
        self.assertFalse(hasattr(result, "authorized_repositories"))


if __name__ == "__main__":
    unittest.main()
