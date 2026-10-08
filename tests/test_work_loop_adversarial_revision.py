"""Adversarial regression cases; execution remains simulation-only."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from orion_v3.work_loop.authorization import issue_authorization, verify_authorization
from orion_v3.work_loop.contracts import EvidenceRecord, Proposal, RiskClass, WorkState
from orion_v3.work_loop.engine import WorkLoopEngine
from orion_v3.work_loop.vault import ProjectVault


def test_revision_mismatch_denied(tmp_path):
    p = Proposal("p", "t", "filesystem.read", str(tmp_path))
    token = issue_authorization(p, RiskClass.GREEN,
        (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat(),
        b"secret", source_revision="commit-a")
    assert verify_authorization(token, p, b"secret", expected_source_revision="commit-a")
    assert not verify_authorization(token, p, b"secret", expected_source_revision="commit-b")


def test_revision_tampering_invalidates_signature(tmp_path):
    p = Proposal("p", "t", "filesystem.read", str(tmp_path))
    token = issue_authorization(p, RiskClass.GREEN,
        (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat(),
        b"secret", source_revision="commit-a")
    assert not verify_authorization(replace(token, source_revision="commit-b"),
                                    p, b"secret", expected_source_revision="commit-b")


def test_caller_trusted_flag_cannot_promote_pass(tmp_path):
    vault = ProjectVault(tmp_path)
    vault.initialize(WorkState("p", "objective", "checkpoint", "t"))
    p = Proposal("p", "t", "filesystem.read", str(vault.repo_path))
    e = EvidenceRecord("p", "t", p.proposal_hash, "execution", "pass", "executor", "rev")
    result = WorkLoopEngine(vault).apply_evidence(
        p, e, required_type="execution", expected_source_revision="rev",
        trusted_verifier_pass=True, next_action_on_pass="advance",
        next_action_on_fail="wait")
    assert not result.state_updated
    assert vault.load().last_verified_result == "none"


def test_revision_bound_token_does_not_authorize_other_proposal(tmp_path):
    p = Proposal("p", "t", "filesystem.read", str(tmp_path))
    token = issue_authorization(p, RiskClass.GREEN,
        (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat(),
        b"secret", source_revision="rev")
    changed = replace(p, task_id="another")
    assert not verify_authorization(token, changed, b"secret", expected_source_revision="rev")
