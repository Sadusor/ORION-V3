"""Offline preflight of contract reviewer: compile patterns and exercise inert fixture."""
import re
import unittest
from task_ledger_trial_001_contract_review import CHECKS, review

class ContractReviewTests(unittest.TestCase):
    def test_all_patterns_compile(self):
        for name, pattern in CHECKS.items():
            with self.subTest(name=name):
                re.compile(pattern, re.I)

    def test_empty_response(self):
        result = review("")
        self.assertEqual(result["blocks"], [])
        self.assertEqual(result["functional_contract"], "NOT_TESTED")
        self.assertEqual(result["execution"], "NOT_RUN")

    def test_fenced_python_parsing(self):
        result = review("task_ledger/app.py\n```python\ndef serve():\n    pass\n```\n")
        self.assertEqual(result["blocks"][0]["syntax"], "VALID")
        self.assertIn("serve", result["blocks"][0]["function_names"])

    def test_invalid_python_does_not_execute(self):
        result = review("file.py\n```python\ndef broken(\n```\n")
        self.assertEqual(result["blocks"][0]["syntax"], "INVALID")
        self.assertEqual(result["execution"], "NOT_RUN")

    def test_no_functional_claim(self):
        result = review("POST /tasks SQLite 409 /health")
        self.assertEqual(result["static_review"], "INDICATORS_ONLY")
        self.assertEqual(result["decision"], "HOLD_ISOLATED_EXECUTION_PENDING_HUMAN_REVIEW")

if __name__ == "__main__":
    unittest.main()
