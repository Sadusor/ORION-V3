import hashlib
from dataclasses import replace
import pytest
from orion_v3.work_loop.contracts import EvidenceRecord, Proposal, WorkState
from orion_v3.work_loop.engine import WorkLoopEngine
from orion_v3.work_loop.vault import ProjectVault


def setup(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "data.txt").write_bytes(b"observed")
    vault = ProjectVault(tmp_path / "vault")
    vault.initialize(WorkState("p", "goal", "checkpoint", "t"))
    proposal = Proposal("p", "t", "filesystem.read", str(workspace), {"path": "data.txt"})
    evidence = EvidenceRecord("p", "t", proposal.proposal_hash, "execution", "pass", "hand", "rev")
    return WorkLoopEngine(vault), vault, proposal, evidence


def test_engine_read_audit_does_not_promote_pass(tmp_path):
    engine, vault, proposal, evidence = setup(tmp_path)
    result = engine.observe_read_evidence(proposal, evidence,
        expected_sha256=hashlib.sha256(b"observed").hexdigest(),
        expected_source_revision="rev")
    assert result.byte_count == 8
    assert vault.load().last_verified_result == "none"
    assert vault.load().next_action == ""


def test_engine_audit_wrong_revision_denied(tmp_path):
    engine, vault, proposal, evidence = setup(tmp_path)
    with pytest.raises(ValueError):
        engine.observe_read_evidence(proposal, replace(evidence, source_revision="wrong"),
            expected_sha256=hashlib.sha256(b"observed").hexdigest(),
            expected_source_revision="rev")
    assert vault.load().last_verified_result == "none"


def test_engine_audit_cannot_verify_write(tmp_path):
    engine, vault, proposal, evidence = setup(tmp_path)
    proposal = replace(proposal, operation="filesystem.write", args={"path":"data.txt","content":"x"})
    evidence = replace(evidence, proposal_hash=proposal.proposal_hash)
    with pytest.raises(ValueError):
        engine.observe_read_evidence(proposal, evidence,
            expected_sha256=hashlib.sha256(b"observed").hexdigest(),
            expected_source_revision="rev")
    assert vault.load().last_verified_result == "none"
