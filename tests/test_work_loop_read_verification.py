import hashlib
from dataclasses import replace
import pytest
from orion_v3.work_loop.contracts import EvidenceRecord, Proposal
from orion_v3.work_loop.read_verification import verify_read_observation


def fixture(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "data.txt").write_bytes(b"orion-test")
    proposal = Proposal("p", "t", "filesystem.read", str(root), {"path": "data.txt"})
    evidence = EvidenceRecord("p", "t", proposal.proposal_hash, "execution", "pass", "hand", "rev")
    return root, proposal, evidence


def test_independent_read_hash(tmp_path):
    root, proposal, evidence = fixture(tmp_path)
    digest = hashlib.sha256(b"orion-test").hexdigest()
    result = verify_read_observation(proposal, evidence, expected_sha256=digest,
                                     expected_source_revision="rev")
    assert result.byte_count == 10
    assert result.sha256 == digest


@pytest.mark.parametrize("mutation", ["wrong_hash", "revision", "task", "verdict", "type", "oversize", "write"])
def test_independent_read_rejects_adversarial_cases(tmp_path, mutation):
    root, proposal, evidence = fixture(tmp_path)
    digest = hashlib.sha256(b"orion-test").hexdigest()
    kwargs = dict(expected_sha256=digest, expected_source_revision="rev")
    if mutation == "wrong_hash":
        kwargs["expected_sha256"] = "0" * 64
    elif mutation == "revision":
        evidence = replace(evidence, source_revision="old")
    elif mutation == "task":
        evidence = replace(evidence, task_id="other")
    elif mutation == "verdict":
        evidence = replace(evidence, verdict="indeterminate")
    elif mutation == "type":
        evidence = replace(evidence, evidence_type="manual")
    elif mutation == "oversize":
        kwargs["max_bytes"] = 2
    elif mutation == "write":
        proposal = replace(proposal, operation="filesystem.write")
    with pytest.raises(ValueError):
        verify_read_observation(proposal, evidence, **kwargs)


def test_symlink_escape_rejected(tmp_path):
    root, proposal, evidence = fixture(tmp_path)
    outside = tmp_path / "secret"
    outside.write_bytes(b"orion-test")
    link = root / "link"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    proposal = replace(proposal, args={"path": "link"})
    evidence = replace(evidence, proposal_hash=proposal.proposal_hash)
    with pytest.raises(ValueError):
        verify_read_observation(proposal, evidence,
            expected_sha256=hashlib.sha256(b"orion-test").hexdigest(),
            expected_source_revision="rev")
