"""Dry-run-only Gitea write boundary: joins qualified components without IO.

The gate and ledger are separate frozen modules. This boundary performs
strict prechecks before consuming a nonce, then returns a receipt only.
It does NOT authorize real writes, network, credential access, or execution.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from .authorization import Authorization
from .contracts import Proposal
from .durable_authorization_ledger_v1 import DurableAuthorizationLedger
from .gitea_authorization_gate_v1 import GiteaAuthorizationGate
from .gitea_write_preflight_v1 import GiteaWriteIntent, build_write_intent

_SHA40 = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True, slots=True)
class DryRunReceipt:
    project_id: str
    task_id: str
    proposal_hash: str
    authorization_nonce: str
    source_revision: str
    status: str = "DRY_RUN_ONLY"


class GiteaDryRunBoundary:
    def __init__(self, ledger: DurableAuthorizationLedger):
        self._ledger = ledger
        self._gate = GiteaAuthorizationGate()

    def qualify(
        self,
        *,
        intent: GiteaWriteIntent,
        proposal: Proposal,
        authorization: Authorization,
        secret: bytes,
        source_revision: str,
        stop_requested: bool,
        owner_approved: bool,
        frozen_paths_clear: bool,
    ) -> DryRunReceipt:
        if stop_requested:
            raise ValueError("STOP active")
        if not owner_approved:
            raise ValueError("owner approval required")
        if not frozen_paths_clear:
            raise ValueError("frozen-path check required")
        if not isinstance(source_revision, str) or not _SHA40.fullmatch(source_revision):
            raise ValueError("invalid source revision")
        if not isinstance(intent, GiteaWriteIntent):
            raise ValueError("invalid write intent")
        # Re-run validation: callers may forge or replace dataclass fields.
        checked = build_write_intent(
            project_id=intent.project_id,
            task_id=intent.task_id,
            repository=intent.repository,
            branch=intent.branch,
            expected_base_sha=intent.expected_base_sha,
            operation=intent.operation,
        )
        if checked != intent:
            raise ValueError("write intent mismatch")
        grant = self._gate.grant(
            intent, proposal, authorization, secret, source_revision=source_revision
        )
        if not self._ledger.reserve(
            nonce=grant.authorization_nonce,
            proposal_hash=grant.proposal_hash,
            source_revision=grant.source_revision,
        ):
            raise ValueError("authorization already consumed")
        return DryRunReceipt(
            project_id=intent.project_id,
            task_id=intent.task_id,
            proposal_hash=grant.proposal_hash,
            authorization_nonce=grant.authorization_nonce,
            source_revision=grant.source_revision,
        )
