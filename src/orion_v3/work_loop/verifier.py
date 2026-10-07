"""Evidence authentication/type checks for the minimal loop."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import EvidenceRecord, Proposal


VALID_EVIDENCE_TYPES = frozenset({"git_check", "execution", "test", "benchmark", "lint", "manual"})
VALID_VERDICTS = frozenset({"pass", "fail", "malformed", "indeterminate"})


@dataclass(frozen=True, slots=True)
class VerificationResult:
    accepted: bool
    verdict: str
    reason: str


def verify_evidence(
    proposal: Proposal,
    evidence: EvidenceRecord,
    *,
    required_type: str | None = None,
    expected_source_revision: str | None = None,
) -> VerificationResult:
    if evidence.project_id != proposal.project_id or evidence.task_id != proposal.task_id:
        return VerificationResult(False, "indeterminate", "evidence belongs to another task")
    if evidence.proposal_hash != proposal.proposal_hash:
        return VerificationResult(False, "indeterminate", "evidence proposal hash mismatch")
    if evidence.evidence_type not in VALID_EVIDENCE_TYPES:
        return VerificationResult(False, "malformed", "unknown evidence type")
    if evidence.verdict not in VALID_VERDICTS:
        return VerificationResult(False, "malformed", "unknown evidence verdict")
    if required_type is not None and evidence.evidence_type != required_type:
        return VerificationResult(False, "indeterminate", "wrong evidence type for transition")
    if expected_source_revision is not None and evidence.source_revision != expected_source_revision:
        return VerificationResult(False, "indeterminate", "source revision mismatch")
    if not evidence.source.strip() or not evidence.source_revision.strip():
        return VerificationResult(False, "malformed", "missing evidence provenance")
    return VerificationResult(True, evidence.verdict, "evidence binding accepted")
