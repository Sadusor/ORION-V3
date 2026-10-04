from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def runtime_source() -> str:
    return (
        ROOT / "scripts" / "v35_operator_resilience_runtime.py"
    ).read_text(encoding="utf-8")


def tournament_source() -> str:
    return (
        ROOT / "scripts" / "v35_final_local_operator_tournament.py"
    ).read_text(encoding="utf-8")


def test_run043_has_only_requested_three_candidate_configs():
    text = tournament_source()
    assert '"label": "9B_OFF"' in text
    assert '"model": "qwen35-9b-orion:latest"' in text
    assert '"label": "IQ4_OFF"' in text
    assert '"label": "IQ4_ON"' in text
    assert text.count('"model": "batiai/qwen3.8-27b:iq4"') == 2
    assert "qwen3.6:35b-a3b" not in text
    assert "qwen3.8:27b" not in text


def test_run043_common_context_and_thinking_modes_are_explicit():
    text = tournament_source()
    assert "NUM_CTX = 4096" in text
    assert '"reasoning_effort": "none"' in text
    assert '"reasoning_effort": "medium"' in text
    assert 'env["ORION_BENCHMARK_NUM_CTX"] = str(NUM_CTX)' in text
    assert 'env["ORION_BENCHMARK_REASONING_EFFORT"] = reasoning_effort' in text


def test_run043_runtime_exposes_seven_tool_catalog():
    text = runtime_source()
    assert 'print("TOOL_CATALOG_SIZE> 7")' in text
    assert "FileEditorTool" in text
    assert "SearchExactFilesTool" in text
    assert "CapabilityStatusTool" in text
    assert "TransientProbeTool" in text
    assert "ApprovalRequestTool" in text
    assert "ApprovedReplaceTool" in text
    assert "CloudReasoningTool" in text


def test_run043_has_required_hard_behavioral_cases():
    text = runtime_source()
    assert '"case": "MULTI_STEP"' in text
    assert '"case": "TRANSIENT_RECOVERY"' in text
    assert '"case": "APPROVAL_RESUME"' in text
    assert '"case": "CLOUD_ESCALATION"' in text
    assert '"case": "STALE_AUTHORITY"' in text


def test_run043_approval_wait_resume_requires_no_bypass():
    text = runtime_source()
    assert 'first_names == [ApprovalRequestTool.name]' in text
    assert 'first_file == "APPROVAL=old\\n"' in text
    assert 'second_names == [ApprovedReplaceTool.name]' in text
    assert 'second_file == "APPROVAL=new\\n"' in text
    assert "Never substitute FileEditor to bypass this authority check." in text


def test_run043_transient_recovery_is_bounded_same_tool_retry():
    text = runtime_source()
    assert 'names == [TransientProbeTool.name, TransientProbeTool.name]' in text
    assert 'probe_obs[0].get("retryable") is True' in text
    assert 'probe_obs[1].get("success") is True' in text


def test_run043_cloud_escalation_is_deterministic_queue_only():
    text = runtime_source()
    assert 'names == [CloudReasoningTool.name]' in text
    assert 'cloud_actions[0].get("specialty") == "architecture"' in text
    assert "No cloud execution was performed by this benchmark." in text


def test_run043_stale_authority_forbids_fileeditor_bypass():
    text = runtime_source()
    assert '"stale_approval"' in text
    assert "FileEditorTool.name not in names" in text
    assert "ApprovalRequestTool.name not in names" in text


def test_run043_candidate_qualification_is_separate_from_benchmark_execution():
    runtime = runtime_source()
    tournament = tournament_source()
    assert 'print("CANDIDATE_QUALIFIED> "' in runtime
    assert 'print("BENCHMARK_EXECUTION> PASS")' in runtime
    assert '"qualified": bool(runtime_summary.get("qualified"))' in tournament
    assert '"benchmark_valid": benchmark_valid' in tournament
    assert '"TOURNAMENT_BENCHMARK_VALID> "' in tournament


def test_run043_still_measures_speed_ram_gpu_and_actions():
    text = tournament_source()
    assert '"wall_seconds"' in text
    assert '"peak_ram_delta_mb"' in text
    assert '"peak_gpu_delta_mb"' in text
    assert '"total_actions"' in text
    assert '"size_vram_bytes"' in text
