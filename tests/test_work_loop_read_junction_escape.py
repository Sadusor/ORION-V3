"""Physical Windows junction regression for ORION's independent read observer."""
import hashlib
import os
import subprocess
import pytest
from orion_v3.work_loop.contracts import EvidenceRecord, Proposal
from orion_v3.work_loop.read_verification import verify_read_observation

@pytest.mark.skipif(os.name != "nt", reason="Windows-only junction regression")
def test_read_observer_denies_junction_escape(tmp_path):
    root = tmp_path / "workspace"
    external = tmp_path / "external"
    root.mkdir()
    external.mkdir()
    (external / "payload.txt").write_bytes(b"not-inside")
    junction = root / "linkdir"
    created = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(junction), str(external)],
        capture_output=True, text=True,
    )
    if created.returncode:
        pytest.skip("junction creation unavailable")
    try:
        p = Proposal("p", "t", "filesystem.read", str(root), {"path": "linkdir/payload.txt"})
        e = EvidenceRecord("p", "t", p.proposal_hash, "execution", "pass", "hand", "rev")
        with pytest.raises(ValueError):
            verify_read_observation(p, e,
                expected_sha256=hashlib.sha256(b"not-inside").hexdigest(),
                expected_source_revision="rev")
    finally:
        junction.rmdir()
