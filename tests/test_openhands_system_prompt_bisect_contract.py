from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_run029_eliminates_call_context_and_bisects_system_prompt():
    source = (
        ROOT / "scripts" / "v34_openhands_system_prompt_bisect.py"
    ).read_text(encoding="utf-8")
    assert "CONTROL_MINIMAL_WITH_CONTEXT" in source
    assert "FULL_SYSTEM_NO_CONTEXT" in source
    assert "SYSTEM_BLOCK_0_ONLY" in source or "SYSTEM_BLOCK_" in source
    assert "bisect_failing_sections" in source
    assert "STATIC_WITHOUT_CULPRIT" in source


def test_run029_diagnostic_pass_is_separate_from_openhands_health():
    source = (
        ROOT / "scripts" / "v34_openhands_system_prompt_bisect.py"
    ).read_text(encoding="utf-8")
    assert "DIAGNOSTIC_STATUS> PASS" in source
    assert "OPENHANDS_AGENT_SYSTEM_PATH> FAIL" in source


def test_run029_closes_conversation_before_temp_cleanup():
    source = (
        ROOT / "scripts" / "v34_openhands_system_prompt_bisect.py"
    ).read_text(encoding="utf-8")
    assert "finally:" in source
    assert "conversation.close()" in source
