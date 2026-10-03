from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_run031_uses_compact_inline_orion_prompt():
    source = (
        ROOT / "scripts" / "v34_openhands_compact_agent_calibration.py"
    ).read_text(encoding="utf-8")
    assert "ORION_COMPACT_PROMPT" in source
    assert "system_prompt=ORION_COMPACT_PROMPT" in source
    assert "CUSTOM_SYSTEM_PROMPT_EXACT> " in source


def test_run031_runs_real_agent_loop_and_requires_terminal_action():
    source = (
        ROOT / "scripts" / "v34_openhands_compact_agent_calibration.py"
    ).read_text(encoding="utf-8")
    assert "conversation.run()" in source
    assert "REAL_AGENT_STRUCTURED_TERMINAL_ACTION> PASS" in source
    assert "EXPECTED_TERMINAL_COMMAND> " in source
    assert "EXPECTED_TERMINAL_OBSERVATION> " in source


def test_run031_closes_conversation_before_temp_cleanup():
    source = (
        ROOT / "scripts" / "v34_openhands_compact_agent_calibration.py"
    ).read_text(encoding="utf-8")
    assert "finally:" in source
    assert "conversation.close()" in source
