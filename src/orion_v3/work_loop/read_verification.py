"""ORION-owned read-only independent verifier for filesystem.read.

A deterministic observation may verify *readable bytes*, not that a Hand
actually performed an operation. Never use this module to approve writes.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import hmac
import os
from pathlib import Path
from .contracts import EvidenceRecord, Proposal
from .paths import require_inside_workspace


@dataclass(frozen=True, slots=True)
class ReadObservation:
    proposal_hash: str
    source_revision: str
    sha256: str
    byte_count: int


def verify_read_observation(proposal: Proposal, evidence: EvidenceRecord, *,
                            expected_sha256: str, expected_source_revision: str,
                            max_bytes: int = 8 * 1024 * 1024) -> ReadObservation:
    if proposal.operation != "filesystem.read":
        raise ValueError("independent read verifier cannot verify execution or writes")
    if evidence.verdict != "pass" or evidence.evidence_type != "execution":
        raise ValueError("read verification requires bound execution PASS evidence")
    if (evidence.project_id != proposal.project_id or
        evidence.task_id != proposal.task_id or
        evidence.proposal_hash != proposal.proposal_hash or
        evidence.source_revision != expected_source_revision):
        raise ValueError("evidence binding mismatch")
    if not isinstance(expected_sha256, str) or len(expected_sha256) != 64:
        raise ValueError("expected SHA256 required")
    try:
        bytes.fromhex(expected_sha256)
    except ValueError as exc:
        raise ValueError("invalid SHA256") from exc
    path = proposal.args.get("path")
    if not isinstance(path, str):
        raise ValueError("missing read path")
    # Reject link traversal even when the final resolved path remains inside
    # the workspace. A preflight check is not an OS sandbox guarantee.
    from .paths import resolved_workspace
    raw_root = resolved_workspace(proposal.workspace)
    raw_candidate = Path(path).expanduser()
    if not raw_candidate.is_absolute():
        raw_candidate = raw_root / raw_candidate
    current = raw_candidate
    while True:
        if current.is_symlink():
            raise ValueError("symlink traversal forbidden")
        if current == raw_root or current == current.parent:
            break
        current = current.parent
    target = require_inside_workspace(path, proposal.workspace)
    if not target.is_file() or target.is_symlink():
        raise ValueError("not a regular non-symlink file")
    if max_bytes < 0 or target.stat().st_size > max_bytes:
        raise ValueError("read size limit exceeded")
    digest = hashlib.sha256()
    count = 0
    before = target.stat()
    with target.open("rb") as handle:
        opened = os.fstat(handle.fileno())
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise ValueError("file replaced before open")
        while chunk := handle.read(min(65536, max_bytes + 1 - count)):
            count += len(chunk)
            if count > max_bytes:
                raise ValueError("read size limit exceeded")
            digest.update(chunk)
        after = os.fstat(handle.fileno())
    current = target.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError("file changed during read")
    if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns):
        raise ValueError("path changed during read")
    observed = digest.hexdigest()
    if not hmac.compare_digest(observed, expected_sha256.lower()):
        raise ValueError("independent hash mismatch")
    return ReadObservation(proposal.proposal_hash, expected_source_revision, observed, count)
