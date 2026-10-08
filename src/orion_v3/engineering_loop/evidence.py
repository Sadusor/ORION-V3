"""Normalize published TheHands GitCheck evidence without granting authority.

This module does not execute code, authorize a Hand, update ORION Vault, or
interpret a PowerShell exit code as independent product acceptance.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

_SHA = re.compile(r"^[0-9a-f]{40}$")
_SESSION = re.compile(r"^[A-Za-z0-9_-]{6,100}$")


class EvidenceContractError(ValueError):
    pass


@dataclass(frozen=True)
class EvidenceAssessment:
    session_id: str
    hand_id: str
    thehands_source_commit: str
    thehands_tree_sha: str
    expected_orion_revision: str
    observed_orion_revision: str | None
    transport_result: str
    product_verdict: str
    reason: str
    next_action: str


def _sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _SHA.fullmatch(value):
        raise EvidenceContractError(f"invalid {field}")
    return value


def assess_cycle(*, session_id: str, expected_orion_revision: str,
                 expected_thehands_commit: str, expected_hand_tree: str,
                 expected_hand_id: str, published: Mapping[str, Any],
                 observed_orion_revision: str | None = None,
                 acceptance_passed: bool = False) -> EvidenceAssessment:
    """Assess one owner-approved run; acceptance_passed is external verifier truth.

    No model, reviewer or script text may set acceptance_passed without a
    separate trusted verifier. This function never performs that verification.
    """
    if not isinstance(session_id, str) or not _SESSION.fullmatch(session_id):
        raise EvidenceContractError("invalid session_id")
    if not isinstance(expected_hand_id, str) or not expected_hand_id.strip():
        raise EvidenceContractError("invalid expected_hand_id")
    orion = _sha(expected_orion_revision, "expected_orion_revision")
    th = _sha(expected_thehands_commit, "expected_thehands_commit")
    tree = _sha(expected_hand_tree, "expected_hand_tree")
    if not isinstance(published, Mapping) or published.get("schema") != "thehands.github-evidence.v1":
        raise EvidenceContractError("unexpected published evidence schema")
    if published.get("evidence_id") != f"thehands-{session_id}":
        raise EvidenceContractError("session evidence mismatch")
    if published.get("hand_id") != expected_hand_id:
        raise EvidenceContractError("hand mismatch")
    if published.get("source_commit") != th or published.get("hand_tree_sha") != tree:
        raise EvidenceContractError("TheHands source/tree mismatch")
    result = published.get("result")
    if result not in ("PASS", "FAIL", "STOPPED"):
        raise EvidenceContractError("unknown TheHands result")
    observed = None if observed_orion_revision is None else _sha(observed_orion_revision, "observed_orion_revision")
    if result == "STOPPED":
        verdict, reason, action = "STOPPED", "owner or session STOP", "review_stop"
    elif result == "FAIL":
        verdict, reason, action = "FAIL", "GitCheck process failed", "repair"
    elif observed != orion:
        verdict, reason, action = "UNVERIFIED", "ORION target revision not independently matched", "verify_revision"
    elif not acceptance_passed:
        verdict, reason, action = "UNVERIFIED", "independent ORION acceptance not established", "verify_acceptance"
    else:
        verdict, reason, action = "PASS", "independent acceptance supplied for matching ORION revision", "document_and_freeze"
    return EvidenceAssessment(session_id, expected_hand_id, th, tree, orion, observed,
                              result, verdict, reason, action)
