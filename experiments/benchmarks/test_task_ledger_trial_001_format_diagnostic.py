"""Offline regression tests for the inert Task Ledger format diagnostic."""
import re
import unittest
from task_ledger_trial_001_format_diagnostic import CONTRACT, diagnose

class DiagnosticTests(unittest.TestCase):
    def test_every_contract_pattern_compiles(self):
        for name, pattern in CONTRACT.items():
            with self.subTest(name=name):
                re.compile(pattern, re.I)

    def test_empty_response_is_safe(self):
        report = diagnose("")
        self.assertEqual(report["classification"], "NO_RECOGNIZED_TEST_FUNCTIONS")
        self.assertEqual(report["execution"], "NOT_RUN")

    def test_recognized_fenced_tests(self):
        response = ("task_ledger/__init__.py\n```python\nVERSION = 1\n```\n"
                    "task_ledger/__main__.py\n```python\ndef main(): pass\n```\n"
                    "tests/test_api.py\n```python\ndef test_one(): assert True\n```\n")
        report = diagnose(response)
        self.assertEqual(report["classification"], "TESTS_RECOGNIZED")
        self.assertEqual(report["test_counts"]["fenced_python_ast"], 1)

    def test_unfenced_test_is_not_misreported_missing(self):
        report = diagnose("def test_outside(): pass")
        self.assertEqual(report["classification"], "TESTS_PRESENT_OUTSIDE_RECOGNIZED_PYTHON_FENCES")

    def test_windows_path(self):
        report = diagnose(r"task_ledger\__main__.py")
        self.assertTrue(report["contract_signals"]["package_entrypoint"])

    def test_no_model_execution(self):
        self.assertEqual(diagnose("import os")["execution"], "NOT_RUN")

if __name__ == "__main__":
    unittest.main()
