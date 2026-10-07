import json

import pytest

from orion_v3.work_loop.contracts import EvidenceRecord, Proposal, WorkState
from orion_v3.work_loop.vault import ProjectVault, VaultError


def state():
    return WorkState(
        project_id="demo",
        objective="prove restart continuity",
        checkpoint="M4",
        current_task="task-1",
        next_action="run deliberate failure",
        constraints=["workspace only"],
        frozen_paths=["repo/frozen"],
    )


def test_vault_round_trip_and_no_overwrite(tmp_path):
    vault = ProjectVault(tmp_path)
    original = state()
    vault.initialize(original)
    loaded = vault.load()
    assert loaded == original
    assert (tmp_path / "repo").is_dir()
    with pytest.raises(VaultError):
        vault.initialize(original)


def test_verified_result_updates_state_and_appends_journal(tmp_path):
    vault = ProjectVault(tmp_path)
    vault.initialize(state())
    proposal = Proposal("demo", "task-1", "filesystem.write", str(tmp_path / "repo"), {"path": "x.txt"})
    evidence = EvidenceRecord(
        "demo", "task-1", proposal.proposal_hash, "execution", "fail",
        "thehands", "deadbeef", "deliberate fixture failure"
    )
    updated = vault.record_verified_result(evidence, next_action="repair fixture")
    assert updated.blocked is True
    assert updated.last_verified_result == "execution:fail"
    journal = vault.journal_path.read_text(encoding="utf-8")
    assert "EXECUTION FAIL" in journal
    assert "deliberate fixture failure" in journal


def test_other_task_evidence_cannot_update_state(tmp_path):
    vault = ProjectVault(tmp_path)
    vault.initialize(state())
    evidence = EvidenceRecord("demo", "other", "x", "execution", "pass", "thehands", "rev")
    with pytest.raises(VaultError):
        vault.record_verified_result(evidence, next_action="bad")
