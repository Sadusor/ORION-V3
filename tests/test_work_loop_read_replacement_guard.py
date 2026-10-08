import hashlib
from orion_v3.work_loop.contracts import EvidenceRecord, Proposal
from orion_v3.work_loop.read_verification import verify_read_observation


def test_read_verifier_still_observes_stable_file(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "stable").write_bytes(b"stable")
    p = Proposal("p", "t", "filesystem.read", str(workspace), {"path": "stable"})
    e = EvidenceRecord("p", "t", p.proposal_hash, "execution", "pass", "hand", "rev")
    observed = verify_read_observation(p, e,
        expected_sha256=hashlib.sha256(b"stable").hexdigest(),
        expected_source_revision="rev")
    assert observed.byte_count == 6
