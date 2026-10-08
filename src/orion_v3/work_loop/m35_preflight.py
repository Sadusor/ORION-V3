"""Milestone 3.5: fixed-action proposal preflight, not a real executor.

This is a fail-closed preparation gate. It never launches a process or writes files.
"""
from __future__ import annotations
from pathlib import Path
from .contracts import Proposal, RiskClass
from .policy import classify_proposal
from .authorization import Authorization, verify_authorization


def validate_disposable_append(
    proposal: Proposal, authorization: Authorization, *,
    secret: bytes, source_revision: str, workspace: Path,
) -> None:
    root = workspace.resolve(strict=True)
    if root.drive.upper() != "E:" or not root.name.startswith("ORION-M35-"):
        raise ValueError("only a disposable E: ORION-M35- workspace is permitted")
    if proposal.workspace != str(root):
        raise ValueError("workspace mismatch")
    if proposal.operation != "filesystem.write" or set(proposal.args) != {"path", "content"}:
        raise ValueError("only fixed filesystem.write operation allowed")
    target = root / "approved.txt"
    if Path(proposal.args["path"]) != target or proposal.args["content"] != "ORION M35 approved fixture\n":
        raise ValueError("unexpected path or content")
    if proposal.requested_network or proposal.requested_install or proposal.requested_system_change:
        raise ValueError("elevated capability requested")
    decision = classify_proposal(proposal)
    if decision.risk != RiskClass.GREEN or not decision.allowed_to_execute:
        raise ValueError("policy denied")
    if not verify_authorization(authorization, proposal, secret, expected_source_revision=source_revision):
        raise ValueError("authorization denied")
