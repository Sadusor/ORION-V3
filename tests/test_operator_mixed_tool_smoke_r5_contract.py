from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_run036u_auto_starts_ollama_before_qwen():
    source = (
        ROOT / "scripts" / "v35_operator_mixed_tool_smoke_r5.py"
    ).read_text(encoding="utf-8")
    assert "def ensure_ollama()" in source
    assert "subprocess.Popen(" in source
    assert '[executable, "serve"]' in source
    assert 'print("OLLAMA_SERVICE> AUTO_STARTED")' in source
    assert "ensure_local_model()" in source


def test_run036u_requires_exact_local_model():
    source = (
        ROOT / "scripts" / "v35_operator_mixed_tool_smoke_r5.py"
    ).read_text(encoding="utf-8")
    assert 'for prefix in ("ollama_chat/", "ollama/")' in source
    assert "Required local model is not available" in source
    assert "LOCAL_MODEL_AVAILABLE> PASS " in source


def test_run036u_preserves_explicit_bridge_allowlist():
    source = (
        ROOT / "scripts" / "v35_operator_mixed_tool_smoke_r5.py"
    ).read_text(encoding="utf-8")
    bridge = source[
        source.index("class SearchExactFilesExecutor"):
        source.index("class SearchExactFilesTool")
    ]
    assert "action.model_dump()" not in bridge
    assert '"exact_names": list(action.exact_names)' in bridge
    assert '"locations": list(action.locations)' in bridge


def test_run036u_preserves_authority_denial_and_four_case_score():
    source = (
        ROOT / "scripts" / "v35_operator_mixed_tool_smoke_r5.py"
    ).read_text(encoding="utf-8")
    assert 'Literal["active_project", "desktop"]' in source
    assert '"locations": ["active_project"]' in source
    assert "MIXED_TOOL_CASES> 4/4 PASS" in source
    assert "AUTHORITY_BYPASS_ATTEMPTS> 0" in source
