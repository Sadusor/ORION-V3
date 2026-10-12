"""Read-only ORION Vault preflight for proposed Gitea task writes.

No HTTP, no credential access, no STOP mutation and no authorization issuance.
This module checks actual canonical Vault state rather than trusting caller
booleans. STOP and approval MUST be supplied by trusted runtime adapters.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .contracts import Proposal, RiskClass
from .gitea_write_preflight_v1 import GiteaWriteIntent, build_write_intent
from .vault import ProjectVault


@dataclass(frozen=True, slots=True)
class LivePreflightReceipt:
    project_id: str
    task_id: str
    proposal_hash: str
    source_revision: str
    verdict: str = "PREFLIGHT_ONLY"


def inspect_live_preflight(
    *,
    vault: ProjectVault,
    intent: GiteaWriteIntent,
    proposal: Proposal,
    source_revision: str,
    stop_is_clear: Callable[[], bool],
    owner_approval_is_valid: Callable[[str, str, str], bool],
    frozen_path_check: Callable[[GiteaWriteIntent, tuple[str, ...]], bool],
) -> LivePreflightReceipt:
    if not isinstance(vault, ProjectVault):
        raise ValueError("canonical project Vault required")
    if not isinstance(intent, GiteaWriteIntent) or not isinstance(proposal, Proposal):
        raise ValueError("typed intent and proposal required")
    # Revalidate dataclass fields, including against forged instances.
    if build_write_intent(
        project_id=intent.project_id, task_id=intent.task_id,
        repository=intent.repository, branch=intent.branch,
        expected_base_sha=intent.expected_base_sha, operation=intent.operation,
    ) != intent:
        raise ValueError("invalid intent")
    state = vault.load()
    if state.blocked:
        raise ValueError("Vault task blocked")
    if (state.project_id != intent.project_id or state.current_task != intent.task_id
            or proposal.project_id != intent.project_id or proposal.task_id != intent.task_id):
        raise ValueError("canonical task mismatch")
    if source_revision != intent.expected_base_sha:
        raise ValueError("source revision mismatch")
    if (proposal.operation != "gitea_write_intent" or proposal.workspace != intent.repository
            or proposal.args != {
                "branch": intent.branch,
                "base_sha": intent.expected_base_sha,
                "operation": intent.operation,
            } or not proposal.requested_network or proposal.requested_install
            or proposal.requested_system_change):
        raise ValueError("proposal does not match write intent")
    # A write requires a YELLOW owner decision; never execute via GREEN.
    from .policy import classify_proposal
    if classify_proposal(proposal, state.frozen_paths).risk != RiskClass.YELLOW:
        raise ValueError("ORION policy did not classify write YELLOW")
    if not stop_is_clear():
        raise ValueError("STOP is active")
    if not owner_approval_is_valid(intent.project_id, intent.task_id, proposal.proposal_hash):
        raise ValueError("owner approval not verified")
    if not frozen_path_check(intent, tuple(state.frozen_paths)):
        raise ValueError("frozen paths not verified")
    # Re-check STOP after external checks. Still not an atomic execution window.
    if not stop_is_clear():
        raise ValueError("STOP activated during preflight")
    return LivePreflightReceipt(intent.project_id, intent.task_id,
                                proposal.proposal_hash, source_revision)
