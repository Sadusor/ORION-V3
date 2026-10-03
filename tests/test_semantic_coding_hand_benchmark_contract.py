from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "scripts" / "v34_openhands_semantic_coding_worker.py"
BENCHMARK = ROOT / "scripts" / "v34_openhands_semantic_coding_benchmark.py"


def test_openhands_semantic_worker_exposes_file_editor_only():
    source = WORKER.read_text(encoding="utf-8")
    assert "FileEditorTool" in source
    assert "TerminalTool" not in source
    assert '"tool_policy": [FileEditorTool.name]' in source


def test_openhands_semantic_worker_rejects_non_loopback_model_endpoint():
    source = WORKER.read_text(encoding="utf-8")
    assert '"http://127.0.0.1:"' in source
    assert '"http://localhost:"' in source
    assert '"non_local_model_endpoint"' in source


def test_openhands_semantic_benchmark_routes_candidate_through_workpackage_executor():
    source = BENCHMARK.read_text(encoding="utf-8")
    assert "factory.patch_artifact(" in source
    assert "board.authorize_execution(" in source
    assert "WorkPackageExecutor(" in source
    assert "executor.run(" in source
    assert 'print("AGENT_EXECUTION_AUTHORITY> NONE")' in source


def test_openhands_worker_uses_pinned_final_response_api():
    worker = ROOT / "scripts" / "v34_openhands_semantic_coding_worker_fixed.py"
    source = worker.read_text(encoding="utf-8")
    assert "get_agent_final_response" in source
    assert ".get_messages()" not in source


def test_benchmark_points_to_corrected_worker():
    source = BENCHMARK.read_text(encoding="utf-8")
    assert "v34_openhands_semantic_coding_worker_fixed.py" in source


def test_openhands_worker_uses_donor_proven_ollama_chat_transport():
    worker = ROOT / "scripts" / "v34_openhands_semantic_coding_worker_fixed.py"
    source = worker.read_text(encoding="utf-8")
    assert '"ollama_chat/"' in source
    assert 'reasoning_effort="none"' in source
