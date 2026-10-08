from pathlib import Path
from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory
import pytest
from orion_v3.work_loop.m35_preflight import validate_disposable_append
from orion_v3.work_loop.contracts import Proposal, RiskClass
from orion_v3.work_loop.authorization import issue_authorization


def test_m35_fixed_action_preflight():
    # Use a real disposable E: fixture; never monkeypatch global Path semantics.
    with TemporaryDirectory(prefix="ORION-M35-", dir=str(Path.cwd())) as directory:
        root = Path(directory).resolve()
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
