"""Run focused pytest-style regression functions with only Python stdlib.

No external dependency, deployment, database mutation, or runtime startup.
"""
from __future__ import annotations
import importlib.util
import inspect
from pathlib import Path
import tempfile
import traceback
import sys

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "test_cursor_repair_cr1.py",
    "test_cursor_repair_relevance.py",
    "test_cursor_repair_sql_understanding.py",
)


def main():
    total = failed = 0
    for filename in FILES:
        path = ROOT / "tests" / filename
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for name, test in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith("test_"):
                continue
            total += 1
            try:
                params = inspect.signature(test).parameters
                if not params:
                    test()
                elif list(params) == ["tmp_path"]:
                    with tempfile.TemporaryDirectory(prefix="orion-cr-") as folder:
                        test(Path(folder))
                else:
                    raise RuntimeError("Unsupported test arguments: " + str(list(params)))
                print("PASS", filename, name, flush=True)
            except Exception:
                failed += 1
                print("FAIL", filename, name, flush=True)
                traceback.print_exc()
    print(f"CURSOR_STDLIB_TESTS> {total - failed}/{total} PASS; {failed} FAIL", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
