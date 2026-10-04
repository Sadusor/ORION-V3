from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def source() -> str:
    return (
        ROOT / "scripts" / "v35_operator_9b_efficiency.py"
    ).read_text(encoding="utf-8")


def test_run041_targets_only_orion_9b():
    text = source()
    assert '"qwen35-9b-orion:latest"' in text
    assert '"qwen3.6:35b-a3b"' not in text
    assert '"qwen3.8:27b"' not in text
    assert '"batiai/qwen3.8-27b:iq4"' not in text


def test_run041_keeps_correctness_as_hard_gate():
    text = source()
    assert '"correctness_pass": exit_code == 0 and not missing' in text
    assert '"MIXED_TOOL_CASES> 4/4 PASS"' in text
    assert '"AUTHORITY_BYPASS_ATTEMPTS> 0"' in text


def test_run041_measures_same_efficiency_metrics():
    text = source()
    assert '"wall_seconds"' in text
    assert '"peak_ram_delta_mb"' in text
    assert '"peak_gpu_delta_mb"' in text
    assert '"ollama_ps_samples"' in text
    assert "--query-gpu=memory.used" in text
    assert "GlobalMemoryStatusEx" in text


def test_run041_emits_single_model_summary():
    text = source()
    assert "ORION_OPERATOR_EFFICIENCY_SUMMARY> " in text
    assert '"schema": "orion.v3.operator-9b-efficiency.v0"' in text
