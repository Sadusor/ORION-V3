from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_run039_exposes_real_numeric_bounds_to_model():
    source = (
        ROOT / "scripts" / "v35_operator_qwen38_iq4_bounded.py"
    ).read_text(encoding="utf-8")
    assert 'Field(default=4, ge=0, le=6' in source
    assert 'Field(default=10, ge=1, le=20' in source
    assert "allowed range is 0 through 6" in source
    assert "allowed range is 1 through 20" in source


def test_run039_orion_lease_remains_independently_bounded():
    source = (
        ROOT / "scripts" / "v35_operator_qwen38_iq4_bounded.py"
    ).read_text(encoding="utf-8")
    assert '"max_depth": 6' in source
    assert '"max_results": 20' in source
    assert "AuthorityGateway(" in source


def test_run039_preserves_same_iq4_model_and_four_case_suite():
    source = (
        ROOT / "scripts" / "v35_operator_qwen38_iq4_bounded_bootstrap.ps1"
    ).read_text(encoding="utf-8")
    assert "$env:ORION_BENCHMARK_MODEL = 'ollama_chat/batiai/qwen3.8-27b:iq4'" in source
    assert "V3-RUN-039" in source

    bench = (
        ROOT / "scripts" / "v35_operator_qwen38_iq4_bounded.py"
    ).read_text(encoding="utf-8")
    assert "MIXED_TOOL_CASES> 4/4 PASS" in bench
    assert "AUTHORITY_BYPASS_ATTEMPTS> 0" in bench
