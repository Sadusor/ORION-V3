"""Bounded adversarial authority batch; no execution enabled."""
import hashlib
from dataclasses import replace
import pytest
from orion_v3.work_loop.contracts import EvidenceRecord, Proposal, WorkState
from orion_v3.work_loop.engine import WorkLoopEngine
from orion_v3.work_loop.vault import ProjectVault, VaultError
from orion_v3.work_loop.verifier import verify_evidence


@pytest.fixture
def case(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "data").write_bytes(b"original")
    vault = ProjectVault(tmp_path / "vault")
    vault.initialize(WorkState("project", "goal", "checkpoint", "task"))
    proposal = Proposal("project", "task", "filesystem.read", str(workspace), {"path": "data"})
    evidence = EvidenceRecord("project", "task", proposal.proposal_hash, "execution", "pass", "hand", "revision")
    return workspace, vault, proposal, evidence


@pytest.mark.parametrize("field,value", [
    ("project_id", "other-project"),
    ("task_id", "other-task"),
    ("proposal_hash", "f" * 64),
    ("source_revision", "wrong-revision"),
    ("evidence_type", "unknown"),
    ("verdict", "not-a-verdict"),
    ("source", ""),
])
def test_malicious_receipt_cannot_advance_state(case, field, value):
    _, vault, proposal, evidence = case
    changed = replace(evidence, **{field: value})
    before = (vault.state_path.read_bytes(), vault.journal_path.read_bytes())
    result = WorkLoopEngine(vault).apply_evidence(
        proposal, changed, required_type="execution",
        expected_source_revision="revision",
        next_action_on_pass="advance", next_action_on_fail="stop",
        trusted_verifier_pass=True,
    )
    assert not result.state_updated
    assert (vault.state_path.read_bytes(), vault.journal_path.read_bytes()) == before


def test_correct_receipt_without_independent_authority_stays_blocked(case):
    _, vault, proposal, evidence = case
    result = WorkLoopEngine(vault).apply_evidence(
        proposal, evidence, required_type="execution",
        expected_source_revision="revision",
        next_action_on_pass="advance", next_action_on_fail="stop",
        trusted_verifier_pass=True,
    )
    assert not result.state_updated
    assert vault.load().last_verified_result == "none"


def test_observed_file_replacement_rejected_without_state_change(case):
    workspace, vault, proposal, evidence = case
    expected = hashlib.sha256(b"original").hexdigest()
    (workspace / "data").write_bytes(b"replaced")
    before = (vault.state_path.read_bytes(), vault.journal_path.read_bytes())
    with pytest.raises(ValueError):
        WorkLoopEngine(vault).observe_read_evidence(
            proposal, evidence, expected_sha256=expected,
            expected_source_revision="revision",
        )
    assert (vault.state_path.read_bytes(), vault.journal_path.read_bytes()) == before


def test_commit_guard_called_once_and_rejects(case):
    _, vault, _, evidence = case
    calls = []
    def guard():
        calls.append(True)
        return False
    before = (vault.state_path.read_bytes(), vault.journal_path.read_bytes())
    with pytest.raises(VaultError):
        vault.record_verified_result(
            replace(evidence, verdict="fail"), next_action="stop",
            blocked=True, commit_guard=guard,
        )
    assert calls == [True]
    assert (vault.state_path.read_bytes(), vault.journal_path.read_bytes()) == before
