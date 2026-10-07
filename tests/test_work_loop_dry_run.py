from datetime import datetime, timedelta, timezone

from orion_v3.work_loop.authorization import issue_authorization
from orion_v3.work_loop.contracts import Proposal, RiskClass
from orion_v3.work_loop.dry_run import DryRunExecutor
from orion_v3.work_loop.executor import ExecutionRequest


def test_dry_run_never_claims_pass(tmp_path):
    secret = b"secret"
    proposal = Proposal("p", "t", "filesystem.write", str(tmp_path), {"path": "x"})
    expiry = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    auth = issue_authorization(proposal, RiskClass.GREEN, expiry, secret)
    evidence = DryRunExecutor(secret=secret, source_revision="rev").execute(ExecutionRequest(proposal, auth))
    assert evidence.verdict == "indeterminate"
    assert "DRY RUN ONLY" in evidence.detail
    assert not (tmp_path / "x").exists()
