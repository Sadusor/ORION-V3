import tempfile
import unittest
from pathlib import Path
from orion_v3.work_loop.groq_trusted_fixture_verifier_v1 import verify_trusted_fixture

class TrustedFixtureVerifierTests(unittest.TestCase):
    def test_three_functional_cases(self):
        with tempfile.TemporaryDirectory() as d:
            result = verify_trusted_fixture(d)
            self.assertEqual(result["returncode"], 0)
            self.assertTrue(result["tests_passed"])
            self.assertEqual(result["untrusted_execution"], "NOT_PERFORMED")
    def test_reject_nonempty_workspace(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "existing.txt").write_text("keep")
            with self.assertRaisesRegex(ValueError, "DEDICATED_EMPTY_DIRECTORY_REQUIRED"):
                verify_trusted_fixture(d)
    def test_reject_missing_workspace(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "DEDICATED_EMPTY_DIRECTORY_REQUIRED"):
                verify_trusted_fixture(Path(d) / "missing")

if __name__ == "__main__":
    unittest.main()
