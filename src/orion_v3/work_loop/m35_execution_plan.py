"""M3.5 owner-authorized disposable execution plan.

Emits a signed, exact-action preflight decision. This module never runs a child
or claims that a native AppContainer fixture executed this particular proposal.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from .contracts import Proposal, RiskClass
from .authorization import issue_authorization
from .m35_preflight import validate_disposable_append


def run_preflight_fixture(base: Path, source_revision: str) -> dict[str, str]:
    base = base.resolve(strict=True)
    if base.drive.upper() != "E:":
        raise ValueError("M3.5 must use E drive")
    with TemporaryDirectory(prefix="ORION-M35-", dir=str(base)) as directory:
        workspace = Path(directory).resolve(strict=True)
        proposal = Proposal(
            project_id="orion-m35-disposable",
            task_id="approved-file-write",
            operation="filesystem.write",
            workspace=str(workspace),
            args={"path": str(workspace / "approved.txt"), "content": "ORION M35 approved fixture\n"},
        )
        secret = __import__("secrets").token_bytes(32)
        expiry = (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat()
        auth = issue_authorization(proposal, RiskClass.GREEN, expiry, secret, source_revision=source_revision)
        validate_disposable_append(proposal, auth, secret=secret, source_revision=source_revision, workspace=workspace)
        if (workspace / "approved.txt").exists():
            raise RuntimeError("preflight unexpectedly executed a write")
        return {"proposal_hash": proposal.proposal_hash, "risk": "green", "execution": "not_started", "workspace_cleanup": "completed"}
