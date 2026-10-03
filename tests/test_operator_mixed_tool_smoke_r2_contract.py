from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_run036r_keeps_real_openjarvis_tool_executor_and_orion_gateway():
    source = (
        ROOT / "scripts" / "v35_operator_mixed_tool_smoke_r2.py"
    ).read_text(encoding="utf-8")
    assert "JarvisToolExecutor(" in source
    assert "build_registered_filesystem_search_tool" in source
    assert "AuthorityGateway(" in source
    assert "LeaseAuthority(" in source


def test_run036r_does_not_require_openjarvis_rust_capability_policy():
    source = (
        ROOT / "scripts" / "v35_operator_mixed_tool_smoke_r2.py"
    ).read_text(encoding="utf-8")
    assert "build_gate1_capability_policy" not in source
    assert "capability_policy=" not in source
    assert "openjarvis_rust" not in source


def test_run036r_preserves_mixed_tool_scoring():
    source = (
        ROOT / "scripts" / "v35_operator_mixed_tool_smoke_r2.py"
    ).read_text(encoding="utf-8")
    assert "MIXED_TOOL_CASES> 4/4 PASS" in source
    assert "WRONG_TOOL_FAMILY_CASES> 0" in source
    assert "AUTHORITY_BYPASS_ATTEMPTS> 0" in source
    assert "FileEditorTool" in source
    assert "CapabilityStatusTool" in source
