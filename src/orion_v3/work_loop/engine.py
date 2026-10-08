"""Pure state-machine seam for Autonomous Work Loop V1.

No model and no Hand are embedded here.  Callers supply a Proposal and later an
EvidenceRecord.  This keeps Qwen and TheHands replaceable and makes the authority
transition independently testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .contracts import EvidenceRecord, Proposal, RiskClass
from .policy import PolicyDecision, classify_proposal
from .vault import ProjectVault
from .verifier import VerificationResult, verify_evidence


@dataclass(frozen=True, slots=True)
class PreparedWork:
    proposal: Proposal
    policy: PolicyDecision


@dataclass(frozen=True, slots=True)
class AppliedEvidence:
    verification: VerificationResult
    state_updated: bool


class WorkLoopEngine:
    def __init__(self, vault: ProjectVault):
        self.vault = vault

    def prepare(self, proposal: Proposal) -> PreparedWork:
        state = self.vault.load()
        if proposal.project_id != state.project_id:
            return PreparedWork(
                proposal,
                PolicyDecision(RiskClass.RED, False, "proposal belongs to another project"),
            )
        if proposal.task_id != state.current_task:
            return PreparedWork(
                proposal,
                PolicyDecision(RiskClass.RED, False, "proposal is not for current task"),
            )
        return PreparedWork(proposal, classify_proposal(proposal, state.frozen_paths))

    def apply_evidence(
        self,
        proposal: Proposal,
        evidence: EvidenceRecord,
        *,
        required_type: str,
        expected_source_revision: str | None,
        next_action_on_pass: str,
        next_action_on_fail: str,
        commit_guard: Callable[[], bool] | None = None,
    ) -> AppliedEvidence:
        prepared = self.prepare(proposal)
        if prepared.policy.risk != RiskClass.GREEN or not prepared.policy.allowed_to_execute:
            return AppliedEvidence(
                VerificationResult(False, "indeterminate", "proposal is RED"),
                False,
            )
        verification = verify_evidence(
            proposal,
            evidence,
            required_type=required_type,
            expected_source_revision=expected_source_revision,
        )
        if not verification.accepted:
            return AppliedEvidence(verification, False)
        next_action = (
            next_action_on_pass if verification.verdict == "pass" else next_action_on_fail
        )
        if commit_guard is not None and not commit_guard():
            return AppliedEvidence(VerificationResult(False, 'indeterminate', 'commit blocked by STOP'), False)
        self.vault.record_verified_result(
            evidence,
            next_action=next_action,
            blocked=verification.verdict != "pass",
        )
        return AppliedEvidence(verification, True)
