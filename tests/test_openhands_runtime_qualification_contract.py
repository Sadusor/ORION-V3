from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_run035_uses_clean_finished_runtime_semantics():
    source = (
        ROOT / "scripts" / "v34_openhands_runtime_qualification.py"
    ).read_text(encoding="utf-8")
    assert '"stuck_detection": False' in source
    assert 'if "FINISHED" not in execution_status.upper()' in source
    assert "OPENHANDS_FINISH_TOOL> " in source
    assert "NOT_USED_ADVISORY" in source


def test_run035_requires_real_terminal_observation_and_candidate_truth():
    source = (
        ROOT / "scripts" / "v34_openhands_runtime_qualification.py"
    ).read_text(encoding="utf-8")
    assert "def terminal_success(" in source
    assert "OPENHANDS_TERMINAL_OBSERVATION> " in source
    assert 'paths != ("src/clamp.py",)' in source
    assert "candidate_functional_check(candidate)" in source
    assert "AGENT_CANDIDATE_RAW_SHA256> " in source


def test_run035_freezes_exact_candidate_bytes_as_file_replace():
    source = (
        ROOT / "scripts" / "v34_openhands_runtime_qualification.py"
    ).read_text(encoding="utf-8")
    assert 'factory.file_artifact(' in source
    assert 'operation=FileOperation.REPLACE' in source
    assert 'file_artifact.sha256 != candidate_sha' in source
    assert '"sha256": candidate_sha' in source
    assert "WORKPACKAGE_FILE_REPLACE> PASS" in source


def test_run035_closes_store_and_requires_full_envelope():
    source = (
        ROOT / "scripts" / "v34_openhands_runtime_qualification.py"
    ).read_text(encoding="utf-8")
    assert "if store is not None:" in source
    assert "store.close()" in source
    assert "ORION_EXECUTION_ENVELOPE> PASS" in source
    assert "ORION_DETERMINISTIC_VERIFIER> PASS" in source
    assert "OPENHANDS_AGENT_RUNTIME_QUALIFIED> PASS" in source
