"""Safe local preflight for submission evaluator, without running untrusted model code."""
from __future__ import annotations
import tempfile
from pathlib import Path
from task_ledger_submission_batch import count_tests,run

def main():
    with tempfile.TemporaryDirectory(prefix="orion-submission-preflight-") as temp:
        root=Path(temp)
        (root/"test_ledger.py").write_text("\n".join(f"def test_case_{i}(): pass" for i in range(20)),encoding="utf-8")
        assert count_tests(root)==20
        print("LEDGER_SUBMISSION_PREFLIGHT> TWENTY_TEST_DISCOVERY_PASS",flush=True)
        try:run(root)
        except ValueError as error:
            assert "task_ledger/__main__.py" in str(error)
        else:raise AssertionError("missing entrypoint accepted")
        print("LEDGER_SUBMISSION_PREFLIGHT> MISSING_ENTRYPOINT_REJECTED_PASS",flush=True)
        (root/"test_ledger.py").write_text("def test_one(): pass\n",encoding="utf-8")
        assert count_tests(root)==1
        print("LEDGER_SUBMISSION_PREFLIGHT> INSUFFICIENT_TEST_DISCOVERY_PASS",flush=True)
    print("LEDGER_SUBMISSION_PREFLIGHT> ALL_PASS",flush=True)

if __name__=="__main__":main()
