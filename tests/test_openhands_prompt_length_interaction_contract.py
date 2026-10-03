from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_run030_compares_length_order_and_prefix_boundary():
    source = (
        ROOT / "scripts" / "v34_openhands_prompt_length_interaction.py"
    ).read_text(encoding="utf-8")
    assert "FULL_HALVES_SWAPPED" in source
    assert "FULL_SECTIONS_REVERSED" in source
    assert "FULL_NEUTRAL_SAME_CHARS" in source
    assert "FIRST_FAILING_PREFIX_COUNT" in source
    assert "BOUNDARY_NEUTRAL_REPLACEMENT" in source


def test_run030_uses_real_agent_prompt_without_agent_step():
    source = (
        ROOT / "scripts" / "v34_openhands_prompt_length_interaction.py"
    ).read_text(encoding="utf-8")
    assert "conversation.send_message(prompt)" in source
    assert "prepare_llm_messages(" in source
    assert "conversation.run()" not in source
    assert "agent.step(" not in source


def test_run030_closes_conversation_and_separates_diagnostic_health():
    source = (
        ROOT / "scripts" / "v34_openhands_prompt_length_interaction.py"
    ).read_text(encoding="utf-8")
    assert "conversation.close()" in source
    assert "DIAGNOSTIC_STATUS> PASS" in source
    assert "OPENHANDS_AGENT_SYSTEM_PATH> FAIL" in source
