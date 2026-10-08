"""Windows reparse-point / symlink confinement diagnostics (read-only).

These tests do not require administrator privileges. If Windows denies symlink
creation, the test asserts fail-closed behavior for a dangling or outside path
and records that physical reparse-point enforcement remains unproven.
"""
import hashlib
import os
from pathlib import Path
import pytest
from orion_v3.work_loop.contracts import Proposal, EvidenceRecord
from orion_v3.work_loop.read_verification import verify_read_observation
from orion_v3.work_loop.paths import require_inside_workspace, WorkspaceViolation


def test_outside_absolute_path_denied(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"secret")
    with pytest.raises(WorkspaceViolation):
        require_inside_workspace(outside, root)


def test_parent_traversal_denied(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    with pytest.raises(WorkspaceViolation):
        require_inside_workspace("../outside.txt", root)


def test_windows_symlink_escape_when_available(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"secret")
    link = root / "link.txt"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError) as exc:
        pytest.skip("Windows symlink privilege unavailable: " + str(exc))
    proposal = Proposal("p", "t", "filesystem.read", str(root), {"path": "link.txt"})
    evidence = EvidenceRecord("p", "t", proposal.proposal_hash, "execution", "pass", "hand", "rev")
    with pytest.raises(ValueError):
        verify_read_observation(proposal, evidence,
            expected_sha256=hashlib.sha256(b"secret").hexdigest(),
            expected_source_revision="rev")


def test_missing_path_fails_closed(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    proposal = Proposal("p", "t", "filesystem.read", str(root), {"path": "missing"})
    evidence = EvidenceRecord("p", "t", proposal.proposal_hash, "execution", "pass", "hand", "rev")
    with pytest.raises(ValueError):
        verify_read_observation(proposal, evidence,
            expected_sha256=hashlib.sha256(b"secret").hexdigest(),
            expected_source_revision="rev")
