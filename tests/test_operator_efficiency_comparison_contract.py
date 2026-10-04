from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def source() -> str:
    return (
        ROOT / "scripts" / "v35_operator_efficiency_comparison.py"
    ).read_text(encoding="utf-8")


def test_run040_compares_exact_three_qualified_models():
    text = source()
    assert '"qwen3.6:35b-a3b"' in text
    assert '"qwen3.8:27b"' in text
    assert '"batiai/qwen3.8-27b:iq4"' in text


def test_run040_preserves_correctness_as_a_hard_gate():
    text = source()
    assert '"correctness_pass": exit_code == 0 and not missing' in text
    assert "if not row[\"correctness_pass\"]" in text
    assert '"MIXED_TOOL_CASES> 4/4 PASS"' in text
    assert '"AUTHORITY_BYPASS_ATTEMPTS> 0"' in text


def test_run040_unloads_models_before_each_measurement():
    text = source()
    assert "def stop_models(" in text
    assert '[ollama, "stop", model]' in text
    assert "stop_models(ollama)" in text


def test_run040_measures_wall_ram_gpu_and_ollama_ps():
    text = source()
    assert '"wall_seconds"' in text
    assert '"peak_ram_delta_mb"' in text
    assert '"peak_gpu_delta_mb"' in text
    assert '"ollama_ps_samples"' in text
    assert "--query-gpu=memory.used" in text
    assert "GlobalMemoryStatusEx" in text


def test_run040_emits_final_machine_readable_summary():
    text = source()
    assert "ORION_OPERATOR_EFFICIENCY_SUMMARY> " in text
    assert '"schema": "orion.v3.operator-efficiency.v0"' in text
