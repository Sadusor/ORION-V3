"""Authoritative STOP source binding (mock source; NOT live runtime proof)."""
import pytest

from orion_v3.work_loop.commit_coordinator import CommitCoordinator, CommitStopped
from orion_v3.work_loop.contracts import EvidenceRecord, WorkState
from orion_v3.work_loop.vault import ProjectVault, VaultError


class Source:
    def __init__(self):
        self.stopped = False
        self.broken = False
        self.calls = 0

    def stop_requested(self):
        self.calls += 1
        if self.broken:
            raise OSError("STOP source unavailable")
        return self.stopped


@pytest.fixture
def case(tmp_path):
    vault = ProjectVault(tmp_path / "vault")
    vault.initialize(WorkState("p", "goal", "checkpoint", "t"))
    evidence = EvidenceRecord("p", "t", "a" * 64, "execution", "fail", "hand", "rev")
    source = Source()
    coordinator = CommitCoordinator(stop_source=source)
    return vault, evidence, source, coordinator


def commit(case, generation=None):
    vault, evidence, source, coordinator = case
    return vault.record_verified_result(
        evidence, next_action="stop", blocked=True,
        commit_coordinator=coordinator,
        expected_generation=coordinator.snapshot() if generation is None else generation,
    )


def test_authoritative_stop_blocks_vault_without_local_stop(case):
    vault, evidence, source, coordinator = case
    before = (vault.state_path.read_bytes(), vault.journal_path.read_bytes())
    source.stopped = True
    with pytest.raises(VaultError, match="STOP"):
        commit(case)
    assert (vault.state_path.read_bytes(), vault.journal_path.read_bytes()) == before
    assert not vault.pending_path.exists()


def test_unavailable_authoritative_source_fails_closed(case):
    vault, evidence, source, coordinator = case
    before = (vault.state_path.read_bytes(), vault.journal_path.read_bytes())
    source.broken = True
    with pytest.raises(VaultError, match="STOP"):
        commit(case)
    assert (vault.state_path.read_bytes(), vault.journal_path.read_bytes()) == before


def test_authoritative_stop_cleared_allows_commit(case):
    vault, evidence, source, coordinator = case
    source.stopped = True
    with pytest.raises(VaultError):
        commit(case)
    source.stopped = False
    assert commit(case).last_verified_result == "execution:fail"
    assert source.calls >= 2


def test_source_is_checked_inside_commit_window(case):
    _, _, source, coordinator = case
    generation = coordinator.snapshot()
    source.stopped = True
    with pytest.raises(CommitStopped):
        with coordinator.commit_window(generation):
            pass


def test_stale_generation_remains_blocked_even_if_source_clear(case):
    vault, evidence, source, coordinator = case
    generation = coordinator.snapshot()
    coordinator.stop()
    coordinator.resume()
    with pytest.raises(VaultError):
        commit(case, generation)
    assert vault.load().last_verified_result == "none"
