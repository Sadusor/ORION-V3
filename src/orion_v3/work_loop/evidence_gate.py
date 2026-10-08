"""Independent ORION-owned evidence gate.

An executor's claimed PASS is never proof. Only a separately supplied
trusted verifier result may authorize a PASS transition. No real verifier is
wired yet, so all executor PASS claims are rejected.
"""
from __future__ import annotations

from .contracts import EvidenceRecord


def independently_verified_pass(evidence: EvidenceRecord, *, trusted_result: bool = False) -> bool:
    return evidence.verdict == "pass" and trusted_result is True
