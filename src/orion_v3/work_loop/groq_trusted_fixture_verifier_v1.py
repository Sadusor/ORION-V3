"""Trusted-fixture functional verification, never model-generated code.

The subprocess runs only a repository-owned deterministic fixture, not arbitrary
text from Groq or a user. Untrusted proposals remain static-only.
"""
import subprocess
import sys
from pathlib import Path

TRUSTED_FIXTURE = """def normalize_task_title(value):
    result = " ".join(value.split())
    if not result:
        raise ValueError("empty")
    return result
"""
TRUSTED_TESTS = """import unittest
from title_normalizer import normalize_task_title
class Checks(unittest.TestCase):
    def test_trim(self):
        self.assertEqual(normalize_task_title("  hello  "), "hello")
    def test_collapse(self):
        self.assertEqual(normalize_task_title("a  b\\nc"), "a b c")
    def test_empty(self):
        with self.assertRaises(ValueError):
            normalize_task_title("  ")
if __name__ == "__main__":
    unittest.main()
"""

def verify_trusted_fixture(directory):
    root = Path(directory).resolve()
    if not root.is_dir() or any(root.iterdir()):
        raise ValueError("DEDICATED_EMPTY_DIRECTORY_REQUIRED")
    (root / "title_normalizer.py").write_text(TRUSTED_FIXTURE, encoding="utf-8")
    (root / "test_title_normalizer.py").write_text(TRUSTED_TESTS, encoding="utf-8")
    proc = subprocess.run([sys.executable, "-I", "-B", "test_title_normalizer.py"],
        cwd=root, capture_output=True, text=True, timeout=15,
        env={"PYTHONIOENCODING": "utf-8"})
    return {"returncode": proc.returncode,
            "tests_passed": proc.returncode == 0 and "Ran 3 tests" in proc.stderr,
            "trusted_fixture_only": True,
            "untrusted_execution": "NOT_PERFORMED"}
