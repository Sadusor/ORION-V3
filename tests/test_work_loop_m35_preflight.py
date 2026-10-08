from pathlib import Path
from datetime import datetime, timedelta, timezone
import pytest
from orion_v3.work_loop.m35_preflight import validate_disposable_append
from orion_v3.work_loop.contracts import Proposal, RiskClass
from orion_v3.work_loop.authorization import issue_authorization


def test_m35_fixed_action_preflight(monkeypatch, tmp_path):
    root = tmp_path / "ORION-M35-fixture"
    root.mkdir()
    # Exercise the exact Windows E: path check without making a real host write.
    class FakeRoot:
        drive = "E:"
        name = "ORION-M35-fixture"
        def __str__(self):
            return str(root)
        def __truediv__(self, child):
            return root / child
    monkeypatch.setattr(Path, "resolve", lambda self, strict=False: FakeRoot() if self == root else self)
    proposal = Proposal("p", "t", "filesystem.write", str(root), {"path": str(root / "approved.txt"), "content": "ORION M35 approved fixture\n"})
    secret = b"m35-test-secret"
    expiry = (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat()
    auth = issue_authorization(proposal, RiskClass.GREEN, expiry, secret, source_revision="rev")
    validate_disposable_append(proposal, auth, secret=secret, source_revision="rev", workspace=root)
    with pytest.raises(ValueError):
        validate_disposable_append(proposal, auth, secret=b"wrong", source_revision="rev", workspace=root)
    bad = Proposal("p", "t", "filesystem.write", str(root), {"path": str(root / "approved.txt"), "content": "other"})
    with pytest.raises(ValueError):
        validate_disposable_append(bad, auth, secret=secret, source_revision="rev", workspace=root)
