import hashlib
import pytest
from orion_v3.work_loop.contracts import EvidenceRecord, Proposal
from orion_v3.work_loop.read_verification import verify_read_observation

def test_linked_file_is_not_independently_verified(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "actual.txt").write_bytes(b"safe")
    link = root / "alias.txt"
    try:
        link.symlink_to(root / "actual.txt")
    except (OSError, NotImplementedError):
        pytest.skip("symbolic links unavailable")
    proposal = Proposal("p", "t", "filesystem.read", str(root), {"path": "alias.txt"})
    evidence = EvidenceRecord("p", "t", proposal.proposal_hash, "execution", "pass", "hand", "rev")
    with pytest.raises(ValueError):
        verify_read_observation(proposal, evidence,
            expected_sha256=hashlib.sha256(b"safe").hexdigest(),
            expected_source_revision="rev")
