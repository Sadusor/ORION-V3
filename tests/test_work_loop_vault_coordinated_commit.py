"""Vault integration with the in-process STOP coordinator."""
from threading import Event, Thread
import pytest
from orion_v3.work_loop.commit_coordinator import CommitCoordinator
from orion_v3.work_loop.contracts import EvidenceRecord, WorkState
from orion_v3.work_loop.vault import ProjectVault, VaultError


@pytest.fixture
def case(tmp_path):
    vault = ProjectVault(tmp_path / "vault")
    vault.initialize(WorkState("p", "goal", "checkpoint", "t"))
    evidence = EvidenceRecord("p", "t", "a" * 64, "execution", "fail", "hand", "rev")
    return vault, evidence


def commit(vault, evidence, coordinator, generation, **kwargs):
    return vault.record_verified_result(
        evidence, next_action="stop", blocked=True,
        commit_coordinator=coordinator, expected_generation=generation, **kwargs
    )


def test_stop_before_commit_preserves_state_and_journal(case):
    vault, evidence = case
    c = CommitCoordinator()
    generation = c.snapshot()
    before = (vault.state_path.read_bytes(), vault.journal_path.read_bytes())
    c.stop()
    with pytest.raises(VaultError):
        commit(vault, evidence, c, generation)
    assert (vault.state_path.read_bytes(), vault.journal_path.read_bytes()) == before
    assert not vault.pending_path.exists()


def test_stale_generation_after_resume_rejected(case):
    vault, evidence = case
    c = CommitCoordinator()
    generation = c.snapshot()
    c.stop()
    c.resume()
    with pytest.raises(VaultError):
        commit(vault, evidence, c, generation)
    assert vault.load().last_verified_result == "none"


def test_coordinated_commit_updates_state_and_journal(case):
    vault, evidence = case
    c = CommitCoordinator()
    result = commit(vault, evidence, c, c.snapshot())
    assert result.last_verified_result == "execution:fail"
    assert "txid=" in vault.journal_path.read_text(encoding="utf-8")


def test_generation_requires_coordinator(case):
    vault, evidence = case
    with pytest.raises(VaultError):
        vault.record_verified_result(
            evidence, next_action="stop", expected_generation=0
        )


def test_coordinator_requires_generation(case):
    vault, evidence = case
    with pytest.raises(VaultError):
        vault.record_verified_result(
            evidence, next_action="stop", commit_coordinator=CommitCoordinator()
        )


def test_stop_waits_for_commit_window_and_then_blocks_next_commit(case):
    vault, evidence = case
    c = CommitCoordinator()
    entered, release, stopped = Event(), Event(), Event()
    errors = []
    def guard():
        entered.set()
        return release.wait(3)
    def writer():
        try:
            commit(vault, evidence, c, c.snapshot(), commit_guard=guard)
        except Exception as exc:
            errors.append(exc)
    def stopper():
        c.stop()
        stopped.set()
    writer_thread = Thread(target=writer)
    writer_thread.start()
    assert entered.wait(3)
    stop_thread = Thread(target=stopper)
    stop_thread.start()
    assert not stopped.wait(0.05)
    release.set()
    writer_thread.join(3)
    stop_thread.join(3)
    assert not errors
    assert stopped.is_set()
    with pytest.raises(VaultError):
        commit(vault, evidence, c, c.snapshot())
