"""Deterministic adversarial replacement tests for the read verifier."""
import hashlib
import os
from unittest.mock import patch
import pytest
from orion_v3.work_loop.contracts import EvidenceRecord, Proposal
from orion_v3.work_loop.read_verification import verify_read_observation


def test_replaced_file_between_stat_and_open_is_rejected(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    target = root / "data"
    target.write_bytes(b"original")
    replacement = root / "replacement"
    replacement.write_bytes(b"original")
    proposal = Proposal("p", "t", "filesystem.read", str(root), {"path": "data"})
    evidence = EvidenceRecord("p", "t", proposal.proposal_hash, "execution", "pass", "hand", "rev")
    original_open = type(target).open
    changed = False

    def swap_before_open(path, *args, **kwargs):
        nonlocal changed
        if path == target and not changed:
            changed = True
            os.replace(replacement, target)
        return original_open(path, *args, **kwargs)

    with patch.object(type(target), "open", swap_before_open):
        with pytest.raises(ValueError, match="replaced before open"):
            verify_read_observation(proposal, evidence,
                expected_sha256=hashlib.sha256(b"original").hexdigest(),
                expected_source_revision="rev")
    assert changed


def test_replacement_guard_never_mutates_vault(tmp_path):
    from orion_v3.work_loop.vault import ProjectVault
    from orion_v3.work_loop.contracts import WorkState
    from orion_v3.work_loop.engine import WorkLoopEngine
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "data").write_bytes(b"one")
    vault = ProjectVault(tmp_path / "vault")
    vault.initialize(WorkState("p", "goal", "checkpoint", "t"))
    proposal = Proposal("p", "t", "filesystem.read", str(root), {"path": "data"})
    evidence = EvidenceRecord("p", "t", proposal.proposal_hash, "execution", "pass", "hand", "rev")
    with pytest.raises(ValueError, match="hash mismatch"):
        WorkLoopEngine(vault).observe_read_evidence(proposal, evidence,
            expected_sha256=hashlib.sha256(b"two").hexdigest(),
            expected_source_revision="rev")
    assert vault.load().last_verified_result == "none"
