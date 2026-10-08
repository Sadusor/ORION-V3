"""Regression: a rejecting Vault commit guard cannot update canonical files."""
import pytest
from orion_v3.work_loop.contracts import EvidenceRecord, WorkState
from orion_v3.work_loop.vault import ProjectVault, VaultError

def test_rejecting_guard_leaves_state_and_journal_unchanged(tmp_path):
    vault = ProjectVault(tmp_path / "vault")
    vault.initialize(WorkState("p", "goal", "checkpoint", "t"))
    before = (vault.state_path.read_bytes(), vault.journal_path.read_bytes())
    evidence = EvidenceRecord("p", "t", "proposal", "execution", "fail", "hand", "rev")
    with pytest.raises(VaultError):
        vault.record_verified_result(evidence, next_action="stop", blocked=True, commit_guard=lambda: False)
    assert (vault.state_path.read_bytes(), vault.journal_path.read_bytes()) == before
    assert not vault.pending_path.exists()
