from orion_v3.work_loop.contracts import Proposal, RiskClass
from orion_v3.work_loop.policy import classify_proposal


def test_unknown_path_key_fails_closed(tmp_path):
    p = Proposal("p", "t", "filesystem.write", str(tmp_path),
                 args={"target": str(tmp_path.parent / "escape"), "content": "x"})
    assert classify_proposal(p).risk == RiskClass.RED


def test_missing_write_target_fails_closed(tmp_path):
    p = Proposal("p", "t", "filesystem.write", str(tmp_path), args={"content": "x"})
    assert classify_proposal(p).risk == RiskClass.RED


def test_outside_path_fails_closed(tmp_path):
    p = Proposal("p", "t", "filesystem.write", str(tmp_path),
                 args={"path": str(tmp_path.parent / "escape"), "content": "x"})
    assert classify_proposal(p).risk == RiskClass.RED


def test_bounded_write_still_green(tmp_path):
    p = Proposal("p", "t", "filesystem.write", str(tmp_path),
                 args={"path": str(tmp_path / "allowed.txt"), "content": "x"})
    assert classify_proposal(p).risk == RiskClass.GREEN
