from orion_v3.work_loop.coordinator import WorkLoopCoordinator
from orion_v3.work_loop.contracts import Proposal, WorkState
from orion_v3.work_loop.vault import ProjectVault


class Stop:
    def __init__(self, active=False):
        self.active = active

    def stop_requested(self):
        return self.active


def make(tmp_path, stopped=False):
    vault = ProjectVault(tmp_path / "project")
    vault.initialize(WorkState(project_id="demo", objective="test", checkpoint="start", current_task="fix"))
    from orion_v3.work_loop.engine import WorkLoopEngine
    return WorkLoopCoordinator(WorkLoopEngine(vault), secret=b"test-only-secret", source_revision="fixture-rev", stop=Stop(stopped)), vault


def proposal(tmp_path, operation="filesystem.read", **flags):
    return Proposal("demo", "fix", operation, str(tmp_path / "project" / "repo"), **flags)


def test_green_dry_run_does_not_claim_pass(tmp_path):
    loop, vault = make(tmp_path)
    result = loop.cycle(proposal(tmp_path))
    assert result.status == "dry_run"
    assert result.evidence.verdict == "indeterminate"
    assert vault.load().last_verified_result == "execution:indeterminate"
    assert vault.load().blocked


def test_stop_blocks_cycle(tmp_path):
    loop, vault = make(tmp_path, stopped=True)
    assert loop.cycle(proposal(tmp_path)).status == "stopped"
    assert vault.load().last_verified_result == "none"


def test_red_denied(tmp_path):
    loop, vault = make(tmp_path)
    assert loop.cycle(proposal(tmp_path, operation="system.shutdown")).status == "denied"
    assert vault.load().last_verified_result == "none"


def test_yellow_requires_owner(tmp_path):
    loop, vault = make(tmp_path)
    assert loop.cycle(proposal(tmp_path, requested_network=True)).status == "awaiting_owner"
    assert vault.load().last_verified_result == "none"


def test_wrong_task_denied(tmp_path):
    loop, vault = make(tmp_path)
    p = Proposal("demo", "wrong", "filesystem.read", str(tmp_path / "project" / "repo"))
    assert loop.cycle(p).status == "denied"
    assert vault.load().last_verified_result == "none"
