from pathlib import Path
from tempfile import TemporaryDirectory
import pytest
from orion_v3.work_loop.contracts import Proposal
from orion_v3.work_loop.m35_binding import bind_fixed_action


def test_exact_manifest_and_rejection():
    with TemporaryDirectory(prefix="ORION-M35-", dir=str(Path.cwd())) as directory:
        root = Path(directory).resolve()
        target = str(root / "approved.txt")
        good = Proposal("p", "t", "filesystem.write", str(root),
                        {"path": target, "content": "ORION M35 approved fixture\n"})
        manifest = bind_fixed_action(good, "rev")
        assert manifest.proposal_hash == good.proposal_hash
        assert manifest.target == target
        assert len(manifest.content_sha256) == 64
        for bad in (
            Proposal("p", "t", "filesystem.write", str(root),
                     {"path": target, "content": "malicious"}),
            Proposal("p", "t", "filesystem.write", str(root),
                     {"path": str(root / "elsewhere.txt"), "content": "ORION M35 approved fixture\n"}),
            Proposal("p", "t", "filesystem.write", str(root),
                     {"path": target, "content": "ORION M35 approved fixture\n"},
                     requested_network=True),
        ):
            with pytest.raises(ValueError):
                bind_fixed_action(bad, "rev")
