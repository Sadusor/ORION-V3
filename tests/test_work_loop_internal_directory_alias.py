import hashlib
import os
import subprocess
import pytest
from orion_v3.work_loop.contracts import EvidenceRecord, Proposal
from orion_v3.work_loop.read_verification import verify_read_observation

@pytest.mark.skipif(os.name != "nt", reason="Windows only")
def test_inside_workspace_directory_alias_rejected(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    directory = workspace / "real"
    directory.mkdir()
    (directory / "data").write_bytes(b"inside")
    alias = workspace / "alias"
    result = subprocess.run(["cmd", "/c", "mklink", "/J", str(alias), str(directory)],
                            capture_output=True, text=True)
    if result.returncode:
        pytest.skip("directory alias creation unavailable")
    try:
        proposal = Proposal("p", "t", "filesystem.read", str(workspace), {"path": "alias/data"})
        evidence = EvidenceRecord("p", "t", proposal.proposal_hash, "execution", "pass", "hand", "rev")
        with pytest.raises(ValueError):
            verify_read_observation(proposal, evidence,
                expected_sha256=hashlib.sha256(b"inside").hexdigest(),
                expected_source_revision="rev")
    finally:
        alias.rmdir()
