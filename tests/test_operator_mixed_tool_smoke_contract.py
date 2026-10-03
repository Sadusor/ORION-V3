from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_run036_exposes_three_real_tool_origins():
    source = (
        ROOT / "scripts" / "v35_operator_mixed_tool_smoke.py"
    ).read_text(encoding="utf-8")
    assert "FileEditorTool" in source
    assert "build_registered_filesystem_search_tool" in source
    assert "JarvisToolExecutor" in source
    assert "inherited_registry_v0" in source
    assert "CapabilityStatusTool" in source


def test_run036_openjarvis_still_runs_through_orion_authority():
    source = (
        ROOT / "scripts" / "v35_operator_mixed_tool_smoke.py"
    ).read_text(encoding="utf-8")
    assert "LeaseAuthority(" in source
    assert "AuthorityGateway(" in source
    assert 'operation_id="filesystem.search"' in source
    assert '"locations": ["active_project"]' in source
    assert "build_gate1_capability_policy" in source


def test_run036_scores_selection_and_denial():
    source = (
        ROOT / "scripts" / "v35_operator_mixed_tool_smoke.py"
    ).read_text(encoding="utf-8")
    for marker in (
        "SEARCH_CASE_TOOL_SELECTION> PASS",
        "STATUS_CASE_TOOL_SELECTION> PASS",
        "EDIT_CASE_TOOL_SELECTION> PASS",
        "DENIED_CASE_TOOL_SELECTION> PASS",
        "DENIED_CASE_AUTHORITY_BYPASS> 0",
        "WRONG_TOOL_FAMILY_CASES> 0",
        "AUTHORITY_BYPASS_ATTEMPTS> 0",
        "MIXED_TOOL_CASES> 4/4 PASS",
    ):
        assert marker in source


def test_run036_does_not_expose_shell_or_terminal():
    source = (
        ROOT / "scripts" / "v35_operator_mixed_tool_smoke.py"
    ).read_text(encoding="utf-8")
    assert "TerminalTool" not in source
    assert "shell.run" not in source
    assert "include_default_tools=[]" in source
