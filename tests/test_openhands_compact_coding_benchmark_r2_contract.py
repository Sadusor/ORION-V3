from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_run033_finish_is_metric_not_candidate_truth():
    source = (
        ROOT / "scripts" / "v34_openhands_compact_coding_benchmark_r2.py"
    ).read_text(encoding="utf-8")
    assert "OPENHANDS_FINISH_USE> " in source
    assert "FAIL_NONBLOCKING" in source
    assert 'raise RuntimeError("agent never emitted Finish")' not in source
    assert "OPERATOR_COMPLETION_RECOGNITION> " in source


def test_run033_still_requires_real_edit_and_verification_tools():
    source = (
        ROOT / "scripts" / "v34_openhands_compact_coding_benchmark_r2.py"
    ).read_text(encoding="utf-8")
    assert 'raise RuntimeError("agent never used FileEditor")' in source
    assert 'raise RuntimeError("agent never used Terminal verification")' in source
    assert 'actual_paths != ("src/clamp.py",)' in source
    assert "candidate_functional_check(candidate)" in source
    assert "AGENT_CANDIDATE_FROZEN_WORKPACKAGE> PASS" in source
    assert "ORION_DETERMINISTIC_VERIFIER> PASS" in source


def test_run033_exposes_agent_diagnostics_and_keeps_bound():
    source = (
        ROOT / "scripts" / "v34_openhands_compact_coding_benchmark_r2.py"
    ).read_text(encoding="utf-8")
    assert "OPENHANDS_EXECUTION_STATUS> " in source
    assert "OPENHANDS_TOOL_CALL_TRACE> " in source
    assert "OPENHANDS_FINAL_CONTENT> " in source
    assert 'MAX_ITERATIONS = int(os.environ.get("ORION_BENCHMARK_MAX_ITERATIONS", "12"))' in source
