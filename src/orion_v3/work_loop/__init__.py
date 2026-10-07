"""Autonomous Work Loop V1 foundation.

This package is deliberately small. It owns project-local work state contracts,
not ORION Memory, TheHands, or global authority.
"""

from .authorization import Authorization, issue_authorization, verify_authorization
from .contracts import EvidenceRecord, Proposal, RiskClass, WorkState
from .engine import AppliedEvidence, PreparedWork, WorkLoopEngine
from .policy import PolicyDecision, classify_proposal
from .sandbox_srt import SrtSandboxPlan, work_hand_plan
from .vault import ProjectVault
from .verifier import VerificationResult, verify_evidence

__all__ = [
    "AppliedEvidence",
    "Authorization",
    "EvidenceRecord",
    "PolicyDecision",
    "PreparedWork",
    "ProjectVault",
    "Proposal",
    "RiskClass",
    "SrtSandboxPlan",
    "VerificationResult",
    "WorkLoopEngine",
    "WorkState",
    "classify_proposal",
    "issue_authorization",
    "verify_authorization",
    "verify_evidence",
    "work_hand_plan",
]
