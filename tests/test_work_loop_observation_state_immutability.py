"""Rejected read observations must not mutate canonical project state."""
import hashlib
from dataclasses import replace

import pytest

from orion_v3.work_loop.contracts import EvidenceRecord, Proposal, WorkState
from orion_v3.work_loop.engine import WorkLoopEngine
from orion_v3.work_loop.vault import ProjectVault


def test_rejected_observations_preserve_state_and_journal(tmp_path):
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
    digest = hashlib.sha256(b"actual").hexdigest()
    cases = [
        (evidence, "0" * 64),
        (replace(evidence, task_id="wrong"), digest),
        (replace(evidence, source_revision="wrong"), digest),
        (replace(evidence, verdict="fail"), digest),
        (replace(evidence, evidence_type="manual"), digest),
    ]
    for item, expected_hash in cases:
        with pytest.raises(ValueError):
            engine.observe_read_evidence(
                proposal, item, expected_sha256=expected_hash,
                expected_source_revision="rev")
        assert vault.state_path.read_bytes() == state_before
        assert vault.journal_path.read_bytes() == journal_before
        assert vault.load().last_verified_result == "none"
