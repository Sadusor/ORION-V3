import unittest
from orion_v3.modules.conversation_verifier_v2 import ConversationVerifierV2, is_explanatory_question

class FakeStrict:
    def deterministic_preflight(self, reply):
        return {"allowed": not reply.startswith("git push"), "reason":"blocked command"}
    def verify(self, goal, reply, model):
        return {"preflight":"pass","preflight_reason":"","quality_state":"blocked",
                "quality_reason":"No specific issue found", "unsupported_claims":[],
                "missing_evidence":[],"needs_escalation":False}

class ConversationVerifierV2Tests(unittest.TestCase):
    def setUp(self):
        self.v=ConversationVerifierV2(strict=FakeStrict())
    def test_informational_question_with_action_word(self):
        self.assertTrue(is_explanatory_question("How does git push work?"))
        result=self.v.verify("How does git push work?","Git sends commits to a remote.","qwen")
        self.assertEqual(result["quality_state"],"pass")
        self.assertTrue(result["needs_escalation"])
    def test_action_request_still_strict(self):
        self.assertFalse(is_explanatory_question("Can you run this?"))
        self.assertEqual(self.v.verify("Can you run this?","No","qwen")["quality_state"],"blocked")
    def test_executable_output_blocked_even_for_explanation(self):
        result=self.v.verify("How does git push work?","git push origin main","qwen")
        self.assertEqual(result["preflight"],"blocked")
    def test_ambiguous_review_has_disclosure(self):
        result=self.v.verify("What is MyGitea2?","It's a forge.","qwen")
        self.assertIn("INCONCLUSIVE",result["quality_reason"])
    def test_existing_pipeline_routes_to_v2(self):
        from orion_v3.modules.gitea_chat_brain_v1 import GiteaChatStreamingBrain
        self.assertIsInstance(GiteaChatStreamingBrain().verifier,ConversationVerifierV2)
if __name__=="__main__":unittest.main()
