"""Crash recovery and transaction safety regression batch.

Tests the existing Vault implementation, without enabling real execution.
"""
import json
from dataclasses import asdict, replace

import pytest

from orion_v3.work_loop.contracts import EvidenceRecord, WorkState
from orion_v3.work_loop.vault import ProjectVault, VaultError


@pytest.fixture
def vault(tmp_path):
    instance = ProjectVault(tmp_path / "vault")
    instance.initialize(WorkState("p", "goal", "checkpoint", "t"))
    return instance


@pytest.fixture
def failure_evidence():
    return EvidenceRecord("p", "t", "proposal", "execution", "fail", "hand", "rev")


def test_recovery_from_pending_transaction(vault, failure_evidence):
    old = vault.load()
    new = replace(old, last_verified_result="execution:fail", next_action="stop", blocked=True)
    vault._write_pending({"entry": "RECOVERY_UNIQUE_EVENT", "state": asdict(new)})
    restored = ProjectVault(vault.root).load()
    assert restored == new
    assert "RECOVERY_UNIQUE_EVENT" in vault.journal_path.read_text(encoding="utf-8")
    assert not vault.pending_path.exists()


def test_pending_recovery_is_idempotent(vault):
    new = replace(vault.load(), last_verified_result="execution:fail", blocked=True)
    vault._write_pending({"entry": "RECOVERY_IDEMPOTENT_EVENT", "state": asdict(new)})
    vault.load()
    first = vault.journal_path.read_bytes()
    vault.load()
    assert vault.journal_path.read_bytes() == first
    assert first.count(b"RECOVERY_IDEMPOTENT_EVENT") == 1


def test_recovery_after_state_written_before_journal(vault):
    new = replace(vault.load(), last_verified_result="execution:fail", blocked=True)
    vault._write_pending({"entry": "RECOVERY_AFTER_STATE_WRITE", "state": asdict(new)})
    vault._write_state(new)
    assert ProjectVault(vault.root).load() == new
    assert vault.journal_path.read_text(encoding="utf-8").count("RECOVERY_AFTER_STATE_WRITE") == 1


def test_recovery_after_journal_written_before_pending_cleanup(vault):
    new = replace(vault.load(), last_verified_result="execution:fail", blocked=True)
    vault._write_pending({"entry": "RECOVERY_AFTER_JOURNAL_WRITE", "state": asdict(new)})
    vault._write_state(new)
    vault.append_journal("RECOVERY_AFTER_JOURNAL_WRITE")
    assert ProjectVault(vault.root).load() == new
    assert vault.journal_path.read_text(encoding="utf-8").count("RECOVERY_AFTER_JOURNAL_WRITE") == 1


def test_rejected_commit_does_not_create_pending(vault, failure_evidence):
    before = (vault.state_path.read_bytes(), vault.journal_path.read_bytes())
    with pytest.raises(VaultError):
        vault.record_verified_result(
            failure_evidence, next_action="stop", blocked=True, commit_guard=lambda: False
        )
    assert (vault.state_path.read_bytes(), vault.journal_path.read_bytes()) == before
    assert not vault.pending_path.exists()


def test_wrong_task_cannot_change_canonical_state(vault, failure_evidence):
    before = (vault.state_path.read_bytes(), vault.journal_path.read_bytes())
    with pytest.raises(VaultError):
        vault.record_verified_result(
            replace(failure_evidence, task_id="other"), next_action="stop", blocked=True
        )
    assert (vault.state_path.read_bytes(), vault.journal_path.read_bytes()) == before


def test_corrupt_pending_transaction_fails_closed(vault):
    vault.pending_path.write_text("{not valid json", encoding="utf-8")
    before = (vault.state_path.read_bytes(), vault.journal_path.read_bytes())
    with pytest.raises((ValueError, json.JSONDecodeError)):
        ProjectVault(vault.root).load()
    assert (vault.state_path.read_bytes(), vault.journal_path.read_bytes()) == before
