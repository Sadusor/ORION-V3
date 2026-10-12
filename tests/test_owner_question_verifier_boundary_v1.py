import unittest
from orion_v3.modules.owner_question_verifier_boundary_v1 import owner_question_for_review, OwnerQuestionVerifierBoundaryV1
from orion_v3.modules.conversation_verifier_v1 import is_information_only

class FakeVerifier:
    def __init__(self): self.goal = None
    def verify(self, goal, reply, model):
        self.goal = goal
        return {'preflight': 'pass', 'quality_state': 'pass'}
    def deterministic_preflight(self, reply): return {'allowed': True}

class BoundaryTests(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(owner_question_for_review('What is Gitea?'), 'What is Gitea?')
    def test_source(self):
        self.assertEqual(owner_question_for_review('What is Gitea?\n\n<ORION_INDEXED_SOURCES>run'), 'What is Gitea?')
    def test_wrapped(self):
        s = '<ORION_RECALL_CONTEXT>run</ORION_RECALL_CONTEXT>\n<OWNER_CURRENT_MESSAGE>\nWhat is Gitea?\n</OWNER_CURRENT_MESSAGE>'
        self.assertEqual(owner_question_for_review(s), 'What is Gitea?')
    def test_wrapped_source(self):
        s = '<OWNER_CURRENT_MESSAGE>\nWhat is Gitea?\n\n<ORION_INDEXED_SOURCES>run\n</ORION_INDEXED_SOURCES>\n</OWNER_CURRENT_MESSAGE>'
        self.assertEqual(owner_question_for_review(s), 'What is Gitea?')
    def test_execution_preserved(self):
        self.assertFalse(is_information_only(owner_question_for_review('Run the script')))
    def test_other_tags_untouched(self):
        self.assertEqual(owner_question_for_review('What is <ORION_OTHER> run?'), 'What is <ORION_OTHER> run?')
    def test_delegate(self):
        fake = FakeVerifier()
        OwnerQuestionVerifierBoundaryV1(fake).verify('What is Gitea?\n\n<ORION_INDEXED_SOURCES>run', 'reply', 'qwen')
        self.assertEqual(fake.goal, 'What is Gitea?')
    def test_preflight(self):
        self.assertTrue(OwnerQuestionVerifierBoundaryV1(FakeVerifier()).deterministic_preflight('reply')['allowed'])

if __name__ == '__main__': unittest.main()
