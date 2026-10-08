"""Offline regression tests for the inert Task Ledger completeness gate."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from task_ledger_trial_001_completeness import check

def submission(count=20):
    tests = "\n".join(f"def test_case_{i}():\n    assert True" for i in range(count))
    return ("task_ledger/__init__.py\n```python\nVERSION = 1\n```\n"
            "task_ledger/__main__.py\n```python\ndef main():\n    return 0\n```\n"
            "tests/test_ledger.py\n```python\n" + tests + "\n```\n")

class CompletenessTests(unittest.TestCase):
    def test_complete_structure(self):
        self.assertEqual(check(submission())["verdict"], "PASS_STATIC_COMPLETENESS")
    def test_missing_tests(self):
        report = check(submission(0))
        self.assertEqual(report["verdict"], "FAIL_INCOMPLETE")
        self.assertIn("fewer_than_20_test_functions", report["issues"])
    def test_missing_entrypoint(self):
        report = check(submission().replace("task_ledger/__main__.py", "other.py"))
        self.assertIn("missing_file_task_ledger/__main__.py", report["issues"])
    def test_invalid_python(self):
        report = check(submission().replace("VERSION = 1", "def broken("))
        self.assertIn("invalid_python_block_1", report["issues"])
    def test_no_fences(self):
        self.assertEqual(check("just prose")["verdict"], "FAIL_INCOMPLETE")
    def test_no_execution(self):
        self.assertEqual(check(submission())["execution"], "NOT_RUN")

if __name__ == "__main__":
    unittest.main()
