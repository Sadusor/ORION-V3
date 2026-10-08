"""A successful independent read observation is not execution authority."""
import hashlib

from orion_v3.work_loop.contracts import EvidenceRecord, Proposal, WorkState
from orion_v3.work_loop.engine import WorkLoopEngine
from orion_v3.work_loop.vault import ProjectVault


def test_valid_read_observation_cannot_promote_execution_pass(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "data").write_bytes(b"actual")
    vault = ProjectVault(tmp_path / "vault")
    vault.initialize(WorkState("p", "goal", "checkpoint", "t"))
    engine = WorkLoopEngine(vault)
    proposal = Proposal("p", "t", "filesystem.read", str(workspace), {"path": "data"})
    evidence = EvidenceRecord("p", "t", proposal.proposal_hash, "execution", "pass", "hand", "rev")
    state_before = vault.state_path.read_bytes()
    journal_before = vault.journal_path.read_bytes()

    observation = engine.observe_read_evidence(
        proposal,
        evidence,
        expected_sha256=hashlib.sha256(b"actual").hexdigest(),
        expected_source_revision="rev",
    )
    assert observation is not None
    assert vault.state_path.read_bytes() == state_before
    assert vault.journal_path.read_bytes() == journal_before

    outcome = engine.apply_evidence(
        proposal,
        evidence,
        required_type="execution",
        expected_source_revision="rev",
        next_action_on_pass="advance",
        next_action_on_fail="stop",
        trusted_verifier_pass=True,
    )
    assert not outcome.state_updated
    assert vault.state_path.read_bytes() == state_before
    assert vault.journal_path.read_bytes() == journal_before
    assert vault.load().last_verified_result == "none"
