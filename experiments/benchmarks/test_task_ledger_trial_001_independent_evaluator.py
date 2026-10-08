"""Synthetic regression fixtures; never run submitted model code."""
import unittest
from task_ledger_trial_001_independent_evaluator import analyze, extract

def pack(files):
    return "".join(f"**{name}**\n\x60\x60\x60python\n{source}\n\x60\x60\x60\n\n" for name, source in files.items())

BASE = {
    "task_ledger/__init__.py": "pass",
    "task_ledger/db.py": "def connect():\n    return 1",
    "task_ledger/app.py": "import sqlite3\ndef app():\n    return 1",
    "task_ledger/__main__.py": "pass",
    "tests/test_api.py": "import sys\ndef test_a():\n    return sys.executable",
}

class EvaluatorTests(unittest.TestCase):
    def check(self, files, expected):
        ids = [x["id"] for x in analyze(pack(files))["findings"]]
        self.assertIn(expected, ids)

    def test_clean_fixture(self):
        self.assertEqual(analyze(pack(BASE))["verdict"], "STATIC_GATE_CLEAR_FUNCTIONAL_UNVERIFIED")

    def test_missing_module(self):
        files = dict(BASE)
        del files["task_ledger/db.py"]
        self.check(files, "MISSING_FILE")

    def test_syntax_error(self):
        files = dict(BASE, **{"task_ledger/app.py": "def bad("})
        self.check(files, "SYNTAX_ERROR")

    def test_missing_sqlite_import(self):
        files = dict(BASE, **{"task_ledger/app.py": "try:\n    pass\nexcept sqlite3.IntegrityError:\n    pass"})
        self.check(files, "UNBOUND_SQLITE3")

    def test_sqlite_import_resolves(self):
        files = dict(BASE, **{"task_ledger/app.py": "import sqlite3\ntry:\n    pass\nexcept sqlite3.IntegrityError:\n    pass"})
        self.assertNotIn("UNBOUND_SQLITE3", [x["id"] for x in analyze(pack(files))["findings"]])

    def test_nonobject_json(self):
        files = dict(BASE, **{"task_ledger/app.py": "def f(payload):\n    return set(payload.keys())"})
        self.check(files, "NON_OBJECT_JSON")

    def test_negative_length(self):
        files = dict(BASE, **{"task_ledger/app.py": "def f(stream, length):\n    return stream.read(length)"})
        self.check(files, "NEGATIVE_CONTENT_LENGTH")

    def test_missing_sys_import(self):
        files = dict(BASE, **{"tests/test_api.py": "def f():\n    return sys.executable"})
        self.check(files, "UNBOUND_SYS")

    def test_memory_db(self):
        files = dict(BASE, **{"task_ledger/db.py": "DEFAULT_DB = ':memory:'\ndef f(path):\n    return sqlite3.connect(path)"})
        self.check(files, "DISCONNECTED_MEMORY_DB")

    def test_no_source_execution(self):
        files = dict(BASE, **{"task_ledger/app.py": "raise RuntimeError('must never execute')"})
        self.assertEqual(analyze(pack(files))["assessment"], "STATIC_ONLY")

    def test_readme_nested_fence_before_tests(self):
        readme = "**README.md**\n```markdown\n# Example\n```bash\npython -m task_ledger\n```\n```\n\n"
        sample = readme + pack(BASE)
        parsed = extract(sample)
        self.assertIn("tests/test_api.py", parsed)
        self.assertEqual(len(parsed), 5)

    def test_real_frozen_submission_test_module(self):
        from task_ledger_trial_001_independent_evaluator import SOURCE
        parsed = extract(SOURCE.read_text(encoding="utf-8"))
        self.assertIn("tests/test_api.py", parsed)
        self.assertIn("sys.executable", parsed["tests/test_api.py"])
        self.assertIn("TRUNCATED_SUBMISSION", [f["id"] for f in analyze(SOURCE.read_text(encoding="utf-8"))["findings"]])

    def test_source_boundaries(self):
        self.assertEqual(len(extract(pack(BASE))), 5)

if __name__ == "__main__":
    unittest.main()
