"""Autonomous Work Loop V1 foundation.

This package is deliberately small.  It owns project-local work state contracts,
not ORION Memory, TheHands, or global authority.
"""

from .contracts import EvidenceRecord, Proposal, RiskClass, WorkState
from .policy import PolicyDecision, classify_proposal
from .vault import ProjectVault
from .verifier import VerificationResult, verify_evidence

__all__ = [
    "EvidenceRecord",
    "PolicyDecision",
    "ProjectVault",
    "Proposal",
    "RiskClass",
    "VerificationResult",
    "WorkState",
    "classify_proposal",
    "verify_evidence",
]
