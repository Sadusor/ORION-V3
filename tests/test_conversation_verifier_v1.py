import unittest
from orion_v3.modules.conversation_verifier_v1 import ConversationVerifierV1, is_information_only

class FakeVerifier:
    def deterministic_preflight(self, reply):
        if reply.startswith("git push"):
            return {"allowed":False,"reason":"Executable command"}
        return {"allowed":True,"reason":""}
    def verify(self, goal, reply, model):
        return {"preflight":"pass","preflight_reason":"",
                "quality_state":"blocked","quality_reason":"TheHands claims need evidence",
                "unsupported_claims":["TheHands is an agent framework"],
                "missing_evidence":["repository source"],"needs_escalation":False}

class ConversationVerifierTests(unittest.TestCase):
    def setUp(self):
        self.v = ConversationVerifierV1(strict=FakeVerifier())
    def test_ordinary_discussion_is_not_hidden(self):
        result=self.v.verify("What is TheHands?","I think it is a framework","qwen")
        self.assertEqual(result["quality_state"],"pass")
        self.assertTrue(result["needs_escalation"])
        self.assertIn("UNVERIFIED",result["quality_reason"])
        self.assertEqual(len(result["unsupported_claims"]),1)
    def test_git_execution_uses_strict_review(self):
        result=self.v.verify("Push the branch to Gitea","I can do it","qwen")
        self.assertEqual(result["quality_state"],"blocked")
    def test_executable_response_is_blocked_even_in_chat(self):
        result=self.v.verify("What is a repository?","git push origin main","qwen")
        self.assertEqual(result["preflight"],"blocked")
    def test_command_question_uses_strict_review(self):
        self.assertFalse(is_information_only("Can you run commands for me?"))
    def test_existing_gitea_chat_wires_conversation_review(self):
        from orion_v3.modules.gitea_chat_brain_v1 import GiteaChatStreamingBrain
        self.assertIsInstance(GiteaChatStreamingBrain().verifier, ConversationVerifierV1)
    def test_normal_question_is_informational(self):
        self.assertTrue(is_information_only("Can you explain internal ORION Hands versus TheHands?"))
if __name__=="__main__":unittest.main()
