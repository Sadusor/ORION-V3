import unittest
from src.orion_v3.modules.orion_understanding_v1 import interpret, rank_source_path


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

    def test_no_authorization_grant(self):
        result = interpret("Find controls in my private repositories")
        self.assertFalse(hasattr(result, "authorized_repositories"))


if __name__ == "__main__":
    unittest.main()
