"""Independent fixture-byte verifier for M4 recovery, NOT a production executor gate.

Only this trusted verifier records its own test PASS after observing disk bytes.
A model/executor-supplied PASS cannot call this API to bypass authority in production.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from .contracts import EvidenceRecord, Proposal
from .engine import WorkLoopEngine
from .paths import require_inside_workspace
from .verifier import verify_evidence


def verify_fixture_and_record(engine: WorkLoopEngine, proposal: Proposal, *,
                              source_revision: str, stop_requested) -> EvidenceRecord:
    prepared = engine.prepare(proposal)
    if not prepared.policy.allowed_to_execute or proposal.operation != "filesystem.write":
        raise ValueError("fixture verifier rejects operation or policy")
    if not callable(stop_requested) or stop_requested():
        raise RuntimeError("STOP before fixture verification")
    target = require_inside_workspace(proposal.args["path"], proposal.workspace)
    workspace = Path(proposal.workspace).resolve(strict=True)
    if target.parent != workspace or target.is_symlink() or not target.is_file():
        raise ValueError("fixture target must be a direct regular file")
    expected = proposal.args["content"].encode("utf-8")
    if len(expected) > 8192 or len(target.read_bytes()) > 8192:
        raise ValueError("fixture exceeds bounded size")
    observed = target.read_bytes()
    if observed != expected or hashlib.sha256(observed).digest() != hashlib.sha256(expected).digest():
        raise ValueError("independent fixture bytes mismatch")
    evidence = EvidenceRecord(proposal.project_id, proposal.task_id, proposal.proposal_hash,
                              "test", "pass", "orion-m4-independent-fixture-verifier",
                              source_revision, "trusted fixture verifier observed exact disk bytes")
    if not verify_evidence(proposal, evidence, required_type="test",
                           expected_source_revision=source_revision).accepted:
        raise ValueError("verifier evidence binding rejected")
    engine.vault.record_verified_result(evidence, next_action="fixture repair verified",
                                        blocked=False, commit_guard=lambda: not stop_requested())
    if engine.vault.load().last_verified_result != "test:pass":
        raise RuntimeError("fixture PASS readback failed")
    return evidence
