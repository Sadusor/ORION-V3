from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_run034_porcelain_parser_preserves_leading_status_space():
    source = (
        ROOT / "scripts" / "v34_openhands_stuck_characterization.py"
    ).read_text(encoding="utf-8")
    assert "def git_raw(" in source
    assert '"--porcelain=v1",' in source
    assert '"-z",' in source
    assert "return run([\"git\", *args], cwd=cwd).stdout" in source
    assert 'path = record[3:].replace("\\\\", "/")' in source


def test_run034_regresses_exact_old_strip_failure():
    sample = " M src/clamp.py\n?? src/__pycache__/clamp.pyc\n"
    old = sample.strip().splitlines()[0][3:]
    assert old == "rc/clamp.py"


def test_run034_prevents_bytecode_and_captures_observations():
    worker = (
        ROOT / "scripts" / "v34_openhands_run034_worker.py"
    ).read_text(encoding="utf-8")
    bench = (
        ROOT / "scripts" / "v34_openhands_stuck_characterization.py"
    ).read_text(encoding="utf-8")
    assert 'os.environ["PYTHONDONTWRITEBYTECODE"] = "1"' in worker
    assert '[sys.executable, "-B", "-c", code]' in bench
    assert '"event_trace": event_trace[-40:]' in worker
    assert '"stuck_diagnostics": stuck_diag' in worker


def test_run034_compares_stuck_detector_on_and_off():
    source = (
        ROOT / "scripts" / "v34_openhands_stuck_characterization.py"
    ).read_text(encoding="utf-8")
    assert "stuck_detection=True" in source
    assert "stuck_detection=False" in source
    assert "CASE_A_CANDIDATE> " in source
    assert "CASE_B_CANDIDATE> " in source
    assert "CASE_B_CLEAN_TERMINATION> " in source
    assert "OPENHANDS_AGENT_RUNTIME_QUALIFIED> " in source
    assert "DIAGNOSTIC_STATUS> PASS" in source
