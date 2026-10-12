"""One-use ORION authorization gate for Gitea write intents.

Purely in-memory, non-executing; NOT a durable authorization ledger.
A production executor must persist nonce consumption atomically across
processes, verify policy/STOP, and re-check revision before any write.
"""
from __future__ import annotations

from dataclasses import dataclass

from .authorization import Authorization, verify_authorization
from .contracts import Proposal, RiskClass
from .gitea_write_preflight_v1 import GiteaWriteIntent


@dataclass(frozen=True, slots=True)
class GiteaWriteGrant:
    intent: GiteaWriteIntent
    proposal_hash: str
    authorization_nonce: str
    source_revision: str


class GiteaAuthorizationGate:
    def __init__(self) -> None:
        self._used: set[str] = set()

    def grant(
        self,
        intent: GiteaWriteIntent,
        proposal: Proposal,
        auth: Authorization,
        secret: bytes,
        *,
        source_revision: str,
    ) -> GiteaWriteGrant:
        if not isinstance(intent, GiteaWriteIntent) or not isinstance(proposal, Proposal):
            raise ValueError("invalid request")
        if not isinstance(source_revision, str) or len(source_revision) != 40:
            raise ValueError("exact source revision required")
        if source_revision != intent.expected_base_sha:
            raise ValueError("stale source revision")
        if proposal.project_id != intent.project_id or proposal.task_id != intent.task_id:
            raise ValueError("scope mismatch")
        if proposal.operation != "gitea_write_intent" or proposal.workspace != intent.repository:
            raise ValueError("wrong proposal operation")
        if proposal.args != {
            "branch": intent.branch,
            "base_sha": intent.expected_base_sha,
            "operation": intent.operation,
        }:
            raise ValueError("proposal arguments mismatch")
        if not proposal.requested_network or auth.risk != RiskClass.YELLOW:
            raise ValueError("Gitea writes require network-class authorization")
        if not auth.nonce or auth.nonce in self._used:
            raise ValueError("replayed authorization")
        if not verify_authorization(auth, proposal, secret, expected_source_revision=source_revision):
            raise ValueError("invalid authorization")
        self._used.add(auth.nonce)
        return GiteaWriteGrant(intent, proposal.proposal_hash, auth.nonce, source_revision)
