from pathlib import Path

from orion_v3.work_loop.contracts import Proposal, RiskClass
from orion_v3.work_loop.paths import WorkspaceViolation, require_inside_workspace
from orion_v3.work_loop.policy import classify_proposal


def proposal(workspace, operation="filesystem.write", **kwargs):
    return Proposal("project", "task", operation, str(workspace), kwargs)


def test_workspace_write_is_green(tmp_path):
    decision = classify_proposal(proposal(tmp_path, path="repo/a.txt", content="test"))
    assert decision.risk == RiskClass.GREEN
    assert decision.allowed_to_execute is True


def test_parent_escape_is_red(tmp_path):
    decision = classify_proposal(proposal(tmp_path, path="../outside.txt"))
    assert decision.risk == RiskClass.RED
    assert decision.allowed_to_execute is False


def test_absolute_escape_is_red(tmp_path):
    outside = tmp_path.parent / "outside.txt"
    decision = classify_proposal(proposal(tmp_path, path=str(outside)))
    assert decision.risk == RiskClass.RED


def test_frozen_overlap_is_red(tmp_path):
    decision = classify_proposal(
        proposal(tmp_path, path="repo/protected/file.txt"),
        frozen_paths=["repo/protected"],
    )
    assert decision.risk == RiskClass.RED


def test_network_and_install_are_yellow(tmp_path):
    p = Proposal("project", "task", "filesystem.write", str(tmp_path), {"path": "a.txt", "content": "test"}, requested_network=True)
    assert classify_proposal(p).risk == RiskClass.YELLOW
    p = Proposal("project", "task", "filesystem.write", str(tmp_path), {"path": "a.txt", "content": "test"}, requested_install=True)
    assert classify_proposal(p).risk == RiskClass.YELLOW


def test_system_operation_is_red(tmp_path):
    assert classify_proposal(proposal(tmp_path, operation="system.registry")).risk == RiskClass.RED


def test_unknown_operation_is_yellow_not_green(tmp_path):
    assert classify_proposal(proposal(tmp_path, operation="mystery.do")).risk == RiskClass.YELLOW
