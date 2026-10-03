from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_run036s_has_deterministic_openjarvis_control():
    source = (
        ROOT / "scripts" / "v35_operator_mixed_tool_smoke_r3.py"
    ).read_text(encoding="utf-8")
    assert "def deterministic_openjarvis_control()" in source
    assert "DIRECT_OPENJARVIS_CONTROL> PASS" in source
    assert '"exact_names": ["pyproject.toml", "gateway.py"]' in source


def test_run036s_exposes_typed_active_project_location():
    source = (
        ROOT / "scripts" / "v35_operator_mixed_tool_smoke_r3.py"
    ).read_text(encoding="utf-8")
    assert 'list[Literal["active_project"]]' in source
    assert "include every requested name" in source


def test_run036s_prints_search_action_and_observation_before_scoring():
    source = (
        ROOT / "scripts" / "v35_operator_mixed_tool_smoke_r3.py"
    ).read_text(encoding="utf-8")
    assert "SEARCH_CASE_ACTION_TRACE> " in source
    assert "SEARCH_CASE_OBSERVATION_TRACE> " in source


def test_run036s_preserves_original_four_case_score():
    source = (
        ROOT / "scripts" / "v35_operator_mixed_tool_smoke_r3.py"
    ).read_text(encoding="utf-8")
    assert "MIXED_TOOL_CASES> 4/4 PASS" in source
    assert "AUTHORITY_BYPASS_ATTEMPTS> 0" in source
