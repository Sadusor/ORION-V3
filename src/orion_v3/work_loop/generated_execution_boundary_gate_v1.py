"""Pre-execution boundary qualification. Never runs untrusted code.

Checks declared boundary evidence only; does not infer sandbox safety from
Python flags, temp folders, AST checks, or provider responses.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class BoundaryEvidence:
    backend: str
    filesystem_denial: bool
    network_denial: bool
    process_tree_stop: bool
    timeout_enforced: bool
    evidence_authenticated: bool
    measured_on_host: bool

REQUIRED_BACKEND = "windows-appcontainer"

def authorize_generated_execution(evidence, *, owner_approved=False):
    if not isinstance(evidence, BoundaryEvidence):
        return {"authorized": False, "reason": "MISSING_BOUNDARY_EVIDENCE"}
    if evidence.backend != REQUIRED_BACKEND:
        return {"authorized": False, "reason": "UNQUALIFIED_BACKEND"}
    checks = (evidence.filesystem_denial, evidence.network_denial,
              evidence.process_tree_stop, evidence.timeout_enforced,
              evidence.evidence_authenticated, evidence.measured_on_host)
    if any(type(x) is not bool or not x for x in checks):
        return {"authorized": False, "reason": "BOUNDARY_NOT_PROVEN"}
    if owner_approved is not True:
        return {"authorized": False, "reason": "OWNER_APPROVAL_REQUIRED"}
    # Deliberately no execution function or runner in this module.
    return {"authorized": False, "reason": "TRUSTED_ATTESTATION_VERIFIER_NOT_IMPLEMENTED"}
