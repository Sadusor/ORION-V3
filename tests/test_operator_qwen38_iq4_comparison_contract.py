from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_run038_uses_same_mixed_tool_architecture():
    source = (
        ROOT / "scripts" / "v35_operator_qwen38_iq4_comparison.py"
    ).read_text(encoding="utf-8")
    assert "FileEditorTool" in source
    assert "JarvisToolExecutor" in source
    assert "AuthorityGateway(" in source
    assert "CapabilityStatusTool" in source
    assert "MIXED_TOOL_CASES> 4/4 PASS" in source
    assert "AUTHORITY_BYPASS_ATTEMPTS> 0" in source


def test_run038_preserves_adapter_and_ollama_guards():
    source = (
        ROOT / "scripts" / "v35_operator_qwen38_iq4_comparison.py"
    ).read_text(encoding="utf-8")
    bridge = source[
        source.index("class SearchExactFilesExecutor"):
        source.index("class SearchExactFilesTool")
    ]
    assert "action.model_dump()" not in bridge
    assert '"exact_names": list(action.exact_names)' in bridge
    assert "def ensure_ollama()" in source
    assert "ensure_local_model()" in source


def test_run038_bootstrap_targets_iq4_variant_only():
    source = (
        ROOT / "scripts" / "v35_operator_qwen38_iq4_comparison_bootstrap.ps1"
    ).read_text(encoding="utf-8")
    assert "$env:ORION_BENCHMARK_MODEL = 'ollama_chat/batiai/qwen3.8-27b:iq4'" in source
    assert "V3-RUN-038" in source
