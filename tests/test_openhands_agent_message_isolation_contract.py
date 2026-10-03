from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_run028_bypasses_agent_step_but_uses_real_prepared_messages():
    source = (
        ROOT / "scripts" / "v34_openhands_agent_message_isolation.py"
    ).read_text(encoding="utf-8")
    assert "conversation.send_message(prompt)" in source
    assert "prepare_llm_messages(" in source
    assert "conversation.run()" not in source
    assert "agent.step(" not in source
    assert "CASE_A_MINIMAL" in source
    assert "CASE_B_AGENT_PREPARED" in source
    assert "CASE_C_NO_SYSTEM" in source


def test_run028_closes_conversation_before_temp_cleanup():
    source = (
        ROOT / "scripts" / "v34_openhands_agent_message_isolation.py"
    ).read_text(encoding="utf-8")
    assert "finally:" in source
    assert "conversation.close()" in source
