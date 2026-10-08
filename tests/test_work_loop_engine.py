from orion_v3.work_loop.contracts import EvidenceRecord, Proposal, RiskClass, WorkState
from orion_v3.work_loop.engine import WorkLoopEngine
from orion_v3.work_loop.vault import ProjectVault


def setup_engine(tmp_path):
    vault = ProjectVault(tmp_path)
    vault.initialize(WorkState("demo", "objective", "M4", "task-1", frozen_paths=["repo/frozen"]))
    return WorkLoopEngine(vault), vault


def test_engine_rejects_wrong_task_before_hand(tmp_path):
    engine, _ = setup_engine(tmp_path)
    proposal = Proposal("demo", "other", "filesystem.write", str(tmp_path), {"path": "repo/x", "content": "fixture"})
    prepared = engine.prepare(proposal)
    assert prepared.policy.risk == RiskClass.RED
    assert prepared.policy.allowed_to_execute is False


def test_engine_applies_bound_execution_pass(tmp_path):
    engine, vault = setup_engine(tmp_path)
    proposal = Proposal("demo", "task-1", "filesystem.write", str(tmp_path), {"path": "repo/x", "content": "fixture"})
    evidence = EvidenceRecord(
        "demo", "task-1", proposal.proposal_hash, "execution", "pass",
        "thehands", "sha123", "physical receipt"
    )
    result = engine.apply_evidence(
        proposal, evidence,
        required_type="execution",
        expected_source_revision="sha123",
        trusted_verifier_pass=True,
        next_action_on_pass="next bounded task",
        next_action_on_fail="repair",
    )
    assert result.state_updated is True
    assert vault.load().last_verified_result == "execution:pass"
    assert vault.load().next_action == "next bounded task"


def test_engine_does_not_apply_gitcheck_as_execution(tmp_path):
    engine, vault = setup_engine(tmp_path)
    proposal = Proposal("demo", "task-1", "filesystem.write", str(tmp_path), {"path": "repo/x", "content": "fixture"})
    evidence = EvidenceRecord(
        "demo", "task-1", proposal.proposal_hash, "git_check", "pass",
        "github", "sha123"
    )
    result = engine.apply_evidence(
        proposal, evidence,
        required_type="execution",
        expected_source_revision="sha123",
        next_action_on_pass="wrong",
        next_action_on_fail="repair",
    )
    assert result.state_updated is False
    assert vault.load().last_verified_result == "none"
