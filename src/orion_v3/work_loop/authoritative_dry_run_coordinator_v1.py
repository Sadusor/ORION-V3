"""Non-executing authoritative STOP and signed-approval qualification.

Uses ORION's existing StopSource and CommitCoordinator; no simulated booleans.
No network, Git, or credential access. This is NOT a production write adapter.
"""
from __future__ import annotations

from dataclasses import dataclass

from .authorization import Authorization
from .commit_coordinator import CommitCoordinator, CommitStopped
from .contracts import Proposal, RiskClass
from .durable_authorization_ledger_v1 import DurableAuthorizationLedger
from .gitea_authorization_gate_v1 import GiteaAuthorizationGate
from .gitea_write_preflight_v1 import GiteaWriteIntent, build_write_intent
from .policy import classify_proposal
from .stop import StopSource
from .vault import ProjectVault


@dataclass(frozen=True, slots=True)
class QualificationReceipt:
    project_id: str
    task_id: str
    proposal_hash: str
    nonce: str
    source_revision: str
    status: str = "QUALIFIED_NO_WRITE"


class AuthoritativeDryRunCoordinator:
    def __init__(self, *, vault: ProjectVault, ledger: DurableAuthorizationLedger,
                 stop_source: StopSource, commit_coordinator: CommitCoordinator,
                 authorization_secret: bytes):
        if stop_source is None or commit_coordinator is None:
            raise ValueError("authoritative STOP and coordinator required")
        if not isinstance(authorization_secret, bytes) or len(authorization_secret) < 16:
            raise ValueError("authorization verification secret required")
        self._vault = vault
        self._ledger = ledger
        self._stop = stop_source
        self._coordinator = commit_coordinator
        self._secret = authorization_secret

    def qualify(self, *, intent: GiteaWriteIntent, proposal: Proposal,
                authorization: Authorization, source_revision: str,
                expected_generation: int) -> QualificationReceipt:
        if not isinstance(intent, GiteaWriteIntent) or not isinstance(proposal, Proposal):
            raise ValueError("invalid intent or proposal")
        checked = build_write_intent(
            project_id=intent.project_id, task_id=intent.task_id,
            repository=intent.repository, branch=intent.branch,
            expected_base_sha=intent.expected_base_sha, operation=intent.operation)
        if checked != intent or source_revision != intent.expected_base_sha:
            raise ValueError("invalid intent or revision")
        # The existing coordinator serializes in-process STOP and this decision.
        # The STOP source must be wired to ORION authority by the runtime.
        try:
            with self._coordinator.commit_window(expected_generation):
                if self._stop.stop_requested():
                    raise ValueError("STOP active")
                state = self._vault.load()
                if state.blocked or state.project_id != intent.project_id or state.current_task != intent.task_id:
                    raise ValueError("canonical Vault task mismatch or blocked")
                if (proposal.project_id != intent.project_id or proposal.task_id != intent.task_id
                        or proposal.requested_install or proposal.requested_system_change):
                    raise ValueError("proposal scope or authority mismatch")
                if classify_proposal(proposal, state.frozen_paths).risk != RiskClass.YELLOW:
                    raise ValueError("policy denied")
                # Intent has no file manifest: refuse commit_files when Vault freezes any paths.
                # A future file-aware module must validate every target, not use a bool.
                if intent.operation == "commit_files" and state.frozen_paths:
                    raise ValueError("frozen paths require file-manifest verification")
                grant = GiteaAuthorizationGate().grant(
                    intent, proposal, authorization, self._secret,
                    source_revision=source_revision)
                if self._stop.stop_requested():
                    raise ValueError("STOP active")
                if not self._ledger.reserve(
                    nonce=grant.authorization_nonce, proposal_hash=grant.proposal_hash,
                    source_revision=grant.source_revision):
                    raise ValueError("replayed authorization")
                return QualificationReceipt(
                    intent.project_id, intent.task_id, grant.proposal_hash,
                    grant.authorization_nonce, source_revision)
        except CommitStopped as exc:
            raise ValueError("STOP or stale generation") from exc
