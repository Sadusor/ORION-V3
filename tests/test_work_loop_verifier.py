from orion_v3.work_loop.contracts import EvidenceRecord, Proposal
from orion_v3.work_loop.verifier import verify_evidence


def base():
    proposal = Proposal("p", "t", "filesystem.write", "/work", {"path": "x"})
    evidence = EvidenceRecord("p", "t", proposal.proposal_hash, "execution", "pass", "thehands", "abc123")
    return proposal, evidence


def test_matching_evidence_is_accepted():
    proposal, evidence = base()
    result = verify_evidence(proposal, evidence, required_type="execution", expected_source_revision="abc123")
    assert result.accepted is True
    assert result.verdict == "pass"


def test_git_check_pass_is_not_execution_pass():
    proposal, evidence = base()
    wrong = EvidenceRecord(
        evidence.project_id, evidence.task_id, evidence.proposal_hash,
        "git_check", "pass", evidence.source, evidence.source_revision
    )
    assert verify_evidence(proposal, wrong, required_type="execution").accepted is False


def test_stale_or_other_proposal_cannot_advance():
    proposal, evidence = base()
    stale = EvidenceRecord("p", "t", "0" * 64, "execution", "pass", "thehands", "abc123")
    assert verify_evidence(proposal, stale).accepted is False


def test_wrong_revision_cannot_advance():
    proposal, evidence = base()
    assert verify_evidence(proposal, evidence, expected_source_revision="different").accepted is False
