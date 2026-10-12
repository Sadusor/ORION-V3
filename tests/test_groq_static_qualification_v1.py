import unittest
from orion_v3.work_loop.groq_static_qualification_v1 import qualify, QualificationError

GOOD = 'def normalize_task_title(value):\n    value = " ".join(value.split())\n    if not value:\n        raise ValueError("empty")\n    return value\n'

class GroqStaticQualificationTests(unittest.TestCase):
    def test_valid_static_only(self):
        self.assertEqual(qualify(GOOD, "Check empty and whitespace-only inputs.")["stage"], "STATIC_ONLY_NOT_EXECUTED")
    def test_replay(self):
        with self.assertRaisesRegex(QualificationError, "REPLAYED_REVIEW"):
            qualify(GOOD, GOOD)
    def test_syntax(self):
        with self.assertRaisesRegex(QualificationError, "SYNTAX_INVALID"):
            qualify("def normalize_task_title(:", "review")
    def test_wrong_function(self):
        with self.assertRaisesRegex(QualificationError, "FUNCTION_CONTRACT"):
            qualify("def other(value):\n    return value\n", "review")
    def test_top_level_side_effect(self):
        with self.assertRaisesRegex(QualificationError, "UNEXPECTED_TOP_LEVEL"):
            qualify("print('hello')\n" + GOOD, "review")
    def test_import(self):
        with self.assertRaisesRegex(QualificationError, "UNTRUSTED_OPERATION"):
            qualify("def normalize_task_title(value):\n    import os\n    return value\n", "review")
    def test_empty(self):
        with self.assertRaisesRegex(QualificationError, "INVALID_PROPOSAL"):
            qualify("", "review")
    def test_oversized(self):
        with self.assertRaisesRegex(QualificationError, "INVALID_PROPOSAL"):
            qualify("x" * 8001, "review")
    def test_same_hashes_different_text(self):
        r = qualify(GOOD, "review")
        self.assertNotEqual(r["proposal_sha256"], r["review_sha256"])

if __name__ == "__main__":
    unittest.main()
