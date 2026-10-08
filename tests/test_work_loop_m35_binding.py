from pathlib import Path
from tempfile import TemporaryDirectory
import pytest
from orion_v3.work_loop.contracts import Proposal
from orion_v3.work_loop.m35_binding import bind_fixed_action, authenticate_manifest, verify_manifest_mac, FixedActionManifest


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


def test_manifest_mac_rejects_tampering_and_wrong_key():
    with TemporaryDirectory(prefix="ORION-M35-", dir=str(Path.cwd())) as directory:
        root = Path(directory).resolve()
        p = Proposal("p", "t", "filesystem.write", str(root),
                     {"path": str(root / "approved.txt"), "content": "ORION M35 approved fixture\n"})
        manifest = bind_fixed_action(p, "rev")
        secret = b"a" * 32
        mac = authenticate_manifest(manifest, secret)
        assert verify_manifest_mac(manifest, secret, mac)
        assert not verify_manifest_mac(manifest, b"b" * 32, mac)
        changed = FixedActionManifest(manifest.proposal_hash, manifest.workspace,
                                      manifest.target, "0" * 64, manifest.source_revision)
        assert not verify_manifest_mac(changed, secret, mac)
        assert not verify_manifest_mac(manifest, secret, "invalid")
