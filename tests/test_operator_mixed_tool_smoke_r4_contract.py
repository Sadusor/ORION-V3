from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_run036t_bridge_forwards_only_explicit_orion_arguments():
    source = (
        ROOT / "scripts" / "v35_operator_mixed_tool_smoke_r4.py"
    ).read_text(encoding="utf-8")
    assert '"exact_names": list(action.exact_names)' in source
    assert '"locations": list(action.locations)' in source
    assert '"recursive": bool(action.recursive)' in source
    assert '"max_depth": int(action.max_depth)' in source
    assert '"max_results": int(action.max_results)' in source
    assert "arguments=json.dumps(forwarded" in source


def test_run036t_framework_kind_cannot_cross_search_bridge():
    source = (
        ROOT / "scripts" / "v35_operator_mixed_tool_smoke_r4.py"
    ).read_text(encoding="utf-8")
    bridge_start = source.index("class SearchExactFilesExecutor")
    bridge_end = source.index("class SearchExactFilesTool")
    bridge = source[bridge_start:bridge_end]
    assert "action.model_dump()" not in bridge
    assert '"kind"' not in bridge


def test_run036t_denial_is_expressible_but_outside_lease():
    source = (
        ROOT / "scripts" / "v35_operator_mixed_tool_smoke_r4.py"
    ).read_text(encoding="utf-8")
    assert 'Literal["active_project", "desktop"]' in source
    assert '"locations": ["active_project"]' in source
    assert "scope_violation" in source


def test_run036t_preserves_direct_control_and_four_case_score():
    source = (
        ROOT / "scripts" / "v35_operator_mixed_tool_smoke_r4.py"
    ).read_text(encoding="utf-8")
    assert "DIRECT_OPENJARVIS_CONTROL> PASS" in source
    assert "SEARCH_CASE_ACTION_TRACE> " in source
    assert "SEARCH_CASE_OBSERVATION_TRACE> " in source
    assert "MIXED_TOOL_CASES> 4/4 PASS" in source
    assert "AUTHORITY_BYPASS_ATTEMPTS> 0" in source
