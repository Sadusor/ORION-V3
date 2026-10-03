from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_run032_worker_uses_compact_prompt_and_mixed_coding_tools():
    source = (
        ROOT / "scripts" / "v34_openhands_compact_coding_worker.py"
    ).read_text(encoding="utf-8")
    assert "ORION_COMPACT_CODING_PROMPT" in source
    assert "system_prompt=ORION_COMPACT_CODING_PROMPT" in source
    assert "Tool(name=FileEditorTool.name)" in source
    assert "Tool(name=TerminalTool.name)" in source
    assert 'include_default_tools=["FinishTool"]' in source
    assert "conversation.run()" in source
    assert "conversation.close()" in source


def test_run032_benchmark_requires_file_editor_terminal_and_finish():
    source = (
        ROOT / "scripts" / "v34_openhands_compact_coding_benchmark.py"
    ).read_text(encoding="utf-8")
    assert '"file_editor" not in tool_calls' in source
    assert '"terminal" not in tool_calls' in source
    assert '"finish" not in tool_calls' in source
    assert "AGENT_CANDIDATE_FROZEN_WORKPACKAGE> PASS" in source
    assert "ORION_EXECUTION_ENVELOPE> PASS" in source
    assert "ORION_DETERMINISTIC_VERIFIER> PASS" in source


def test_run032_remains_disposable_and_exact_sha_bounded():
    source = (
        ROOT / "scripts" / "v34_openhands_compact_coding_benchmark.py"
    ).read_text(encoding="utf-8")
    assert 'git(candidate, "rev-parse", "HEAD") == base_sha' in source
    assert 'actual_paths != ("src/clamp.py",)' in source
    assert '"worktree", "add", "--detach"' in source
    assert "AGENT_EXECUTION_AUTHORITY> NONE" in source
