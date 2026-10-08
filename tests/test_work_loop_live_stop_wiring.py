"""Work Loop source wiring: no separate STOP authority is created."""
from orion_v3.work_loop.coordinator import WorkLoopCoordinator
from orion_v3.work_loop.contracts import Proposal, WorkState
from orion_v3.work_loop.engine import WorkLoopEngine
from orion_v3.work_loop.vault import ProjectVault


class Stop:
    def __init__(self):
        self.active = False
        self.calls = 0

    def stop_requested(self):
        self.calls += 1
        return self.active


def make(tmp_path):
    vault = ProjectVault(tmp_path / "project")
    vault.initialize(WorkState("demo", "goal", "start", "fix"))
    stop = Stop()
    loop = WorkLoopCoordinator(WorkLoopEngine(vault), secret=b"test-only-secret",
                               source_revision="fixture-rev", stop=stop)
    proposal = Proposal("demo", "fix", "filesystem.read", str(vault.repo_path))
    return loop, vault, stop, proposal


def test_coordinator_reuses_supplied_authoritative_stop_source(tmp_path):
    loop, vault, stop, proposal = make(tmp_path)
    assert loop.commit_coordinator._stop_source is stop
    assert loop.cycle(proposal).status == "dry_run"
    assert stop.calls >= 4


def test_stop_before_cycle_keeps_vault_unchanged(tmp_path):
    loop, vault, stop, proposal = make(tmp_path)
    stop.active = True
    assert loop.cycle(proposal).status == "stopped"
    assert vault.load().last_verified_result == "none"


def test_stop_flips_at_commit_window_and_blocks_vault(tmp_path):
    loop, vault, stop, proposal = make(tmp_path)
    original = loop.commit_coordinator.commit_window
    from contextlib import contextmanager
    @contextmanager
    def flip(expected_generation):
        stop.active = True
        with original(expected_generation):
            yield
    loop.commit_coordinator.commit_window = flip
    before = (vault.state_path.read_bytes(), vault.journal_path.read_bytes())
    result = loop.cycle(proposal)
    assert result.status == "stopped"
    assert (vault.state_path.read_bytes(), vault.journal_path.read_bytes()) == before
    assert not vault.pending_path.exists()
