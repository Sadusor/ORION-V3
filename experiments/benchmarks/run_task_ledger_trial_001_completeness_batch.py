"""Offline regression then saved-response completeness, without executing model code."""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

def main() -> int:
    tests = HERE / "test_task_ledger_trial_001_completeness.py"
    gate = HERE / "task_ledger_trial_001_completeness.py"
    print("LEDGER_BATCH> REGRESSION_START", flush=True)
    completed = subprocess.run([sys.executable, "-B", str(tests)], cwd=str(HERE),
                               timeout=45, check=False)
    if completed.returncode != 0:
        print("LEDGER_BATCH> REGRESSION_FAIL", flush=True)
        return 1
    print("LEDGER_BATCH> REGRESSION_PASS", flush=True)
    print("LEDGER_BATCH> COMPLETENESS_START", flush=True)
    completed = subprocess.run([sys.executable, "-B", str(gate)], cwd=str(HERE),
                               timeout=45, check=False)
    if completed.returncode != 0:
        print("LEDGER_BATCH> COMPLETENESS_ERROR", flush=True)
        return 1
    print("LEDGER_BATCH> INSPECTION_COMPLETED_CHECK_VERDICT", flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
