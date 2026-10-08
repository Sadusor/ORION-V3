"""Deterministic GREEN/YELLOW/RED classifier for Work Loop V1."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .contracts import Proposal, RiskClass
from .paths import WorkspaceViolation, overlaps_frozen_path, require_inside_workspace


READ_ONLY_OPERATIONS = frozenset({"filesystem.read", "filesystem.list", "filesystem.search", "git.status", "git.diff"})
WORKSPACE_WRITE_OPERATIONS = frozenset({"filesystem.write", "filesystem.mkdir", "filesystem.delete", "git.add", "git.commit"})
RED_OPERATIONS = frozenset({"system.registry", "system.service", "system.shutdown", "credential.read", "policy.modify", "stop.modify"})


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    risk: RiskClass
    allowed_to_execute: bool
    reason: str


def _proposal_paths(proposal: Proposal) -> list[str]:
    values: list[str] = []
    for key in ("path", "paths", "destination", "source"):
        value = proposal.args.get(key)
        if isinstance(value, str):
            values.append(value)
        elif isinstance(value, list):
            values.extend(item for item in value if isinstance(item, str))
    return values


def classify_proposal(proposal: Proposal, frozen_paths: list[str] | None = None) -> PolicyDecision:
    frozen_paths = frozen_paths or []
    schemas = {
        "filesystem.read": {"path"}, "filesystem.list": {"path"},
        "filesystem.search": {"path", "query"},
        "filesystem.write": {"path", "content"},
        "filesystem.mkdir": {"path"}, "filesystem.delete": {"path"},
        "git.status": set(), "git.diff": set(),
        "git.add": {"paths"}, "git.commit": {"message"},
    }
    if proposal.operation in schemas:
        if set(proposal.args) - schemas[proposal.operation]:
            return PolicyDecision(RiskClass.RED, False, "unknown argument key")
        if proposal.operation in {"filesystem.write", "filesystem.mkdir", "filesystem.delete"} and not isinstance(proposal.args.get("path"), str):
            return PolicyDecision(RiskClass.RED, False, "required path missing or malformed")
        if "path" in proposal.args and not isinstance(proposal.args["path"], str):
            return PolicyDecision(RiskClass.RED, False, "path must be text")
        if proposal.operation == "filesystem.write" and not isinstance(proposal.args.get("content"), str):
            return PolicyDecision(RiskClass.RED, False, "required content missing or malformed")
        if proposal.operation == "git.add" and (
            not isinstance(proposal.args.get("paths"), list)
            or not proposal.args["paths"]
            or any(not isinstance(p, str) for p in proposal.args["paths"])
        ):
            return PolicyDecision(RiskClass.RED, False, "required paths missing or malformed")
        if proposal.operation == "git.commit" and not isinstance(proposal.args.get("message"), str):
            return PolicyDecision(RiskClass.RED, False, "required message missing or malformed")
        if proposal.operation == "filesystem.search" and not isinstance(proposal.args.get("query"), str):
            return PolicyDecision(RiskClass.RED, False, "required query missing or malformed")

    if proposal.requested_system_change or proposal.operation in RED_OPERATIONS:
        return PolicyDecision(RiskClass.RED, False, "system/authority operation is RED")

    try:
        for path in _proposal_paths(proposal):
            require_inside_workspace(path, proposal.workspace)
            if overlaps_frozen_path(path, proposal.workspace, frozen_paths):
                return PolicyDecision(RiskClass.RED, False, "target overlaps a frozen path")
    except WorkspaceViolation as exc:
        return PolicyDecision(RiskClass.RED, False, str(exc))

    if proposal.requested_install or proposal.requested_network:
        return PolicyDecision(RiskClass.YELLOW, False, "install/network requires owner decision")

    if proposal.operation in READ_ONLY_OPERATIONS:
        return PolicyDecision(RiskClass.GREEN, True, "bounded read-only operation")

    if proposal.operation in WORKSPACE_WRITE_OPERATIONS:
        return PolicyDecision(RiskClass.GREEN, True, "bounded workspace operation")

    return PolicyDecision(RiskClass.YELLOW, False, "unknown operation requires owner decision")
