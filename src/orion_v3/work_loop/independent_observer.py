"""ORION-owned deterministic observation of read-only workspace state.

A model or executor cannot supply this result: ORION hashes bytes itself.
This does not certify real execution and cannot authorize a write PASS.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
from .contracts import Proposal


def observe_read_hash(proposal: Proposal) -> str:
    if proposal.operation != "filesystem.read":
        raise ValueError("only read observation supported")
    from .paths import require_inside_workspace
    path = proposal.args.get("path")
    if not isinstance(path, str):
        raise ValueError("read observation needs a path")
    target = require_inside_workspace(path, proposal.workspace)
    if not target.is_file():
        raise ValueError("target is not a file")
    return hashlib.sha256(target.read_bytes()).hexdigest()
