from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def decision_source() -> str:
    return (
        ROOT / "scripts" / "v35_fast_good_low_consumption.py"
    ).read_text(encoding="utf-8")


def runtime_source() -> str:
    return (
        ROOT / "scripts" / "v35_operator_bounded_runtime.py"
    ).read_text(encoding="utf-8")


def test_run042_has_all_five_candidate_configs():
    text = decision_source()
    assert '"label": "9B_OFF"' in text
    assert '"model": "qwen35-9b-orion:latest"' in text
    assert '"label": "35B_OFF"' in text
    assert '"label": "27B_OFF"' in text
    assert '"label": "IQ4_OFF"' in text
    assert '"label": "IQ4_ON"' in text
    assert text.count('"model": "batiai/qwen3.8-27b:iq4"') == 2


def test_run042_controls_context_for_every_candidate():
    text = decision_source()
    assert "NUM_CTX = 4096" in text
    assert 'env["ORION_BENCHMARK_NUM_CTX"] = str(NUM_CTX)' in text
    assert '"context_verified": context_ok' in text
    assert 'int(runtime.get("context_length") or 0) == NUM_CTX' in text


def test_run042_compares_iq4_thinking_off_and_on():
    text = decision_source()
    assert '"label": "IQ4_OFF"' in text
    assert '"reasoning_effort": "none"' in text
    assert '"label": "IQ4_ON"' in text
    assert '"reasoning_effort": "medium"' in text


def test_runtime_proves_pinned_litellm_think_mapping():
    text = runtime_source()
    assert "litellm.OllamaChatConfig(num_ctx=NUM_CTX)" in text
    assert 'mapped = litellm.OllamaChatConfig().map_openai_params(' in text
    assert '{"reasoning_effort": REASONING_EFFORT}' in text
    assert 'print("OLLAMA_THINK_MAPPED> "' in text
    assert "reasoning_effort=REASONING_EFFORT" in text


def test_run042_keeps_correctness_and_authority_as_hard_metrics():
    text = decision_source()
    assert '"MIXED_TOOL_CASES> 4/4 PASS"' in text
    assert '"WRONG_TOOL_FAMILY_CASES> 0"' in text
    assert '"AUTHORITY_BYPASS_ATTEMPTS> 0"' in text
    assert '"correctness_pass": exit_code == 0 and not missing and context_ok' in text


def test_run042_measures_speed_ram_gpu_actions_and_runtime_residency():
    text = decision_source()
    assert '"wall_seconds"' in text
    assert '"peak_ram_delta_mb"' in text
    assert '"peak_gpu_delta_mb"' in text
    assert '"actions"' in text
    assert '"size_vram_bytes"' in text
    assert '"context_length"' in text
    assert "ollama_ps_samples" in text


def test_run042_finishes_all_candidates_then_fails_if_any_candidate_fails():
    text = decision_source()
    assert '"FAILED_CANDIDATES> "' in text
    assert 'if failed_labels:' in text
    assert 'print("STATUS> FAIL")' in text
