"""Safe, deterministic coordinator for the existing Work Loop modules.

This module deliberately does not launch a subprocess or modify source files.
A real Work Hand must remain disabled until isolation is independently proven.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .authorization import issue_authorization
from .contracts import EvidenceRecord, Proposal, RiskClass
from .dry_run import DryRunExecutor
from .engine import WorkLoopEngine
from .executor import ExecutionRequest
from .stop import StopSource


@dataclass(frozen=True, slots=True)
class CycleOutcome:
    status: str
    reason: str
    evidence: EvidenceRecord | None = None


class WorkLoopCoordinator:
    """Connect the existing policy, authorization, executor and verifier seams."""

    def __init__(self, engine: WorkLoopEngine, *, secret: bytes, source_revision: str, stop: StopSource):
        self.engine = engine
        self.secret = secret
        self.source_revision = source_revision
        self.stop = stop
        self.executor = DryRunExecutor(secret=secret, source_revision=source_revision)

    def cycle(self, proposal: Proposal) -> CycleOutcome:
        if self.stop.stop_requested():
            return CycleOutcome("stopped", "authoritative STOP requested")
        prepared = self.engine.prepare(proposal)
        if prepared.policy.risk == RiskClass.RED:
            return CycleOutcome("denied", prepared.policy.reason)
        if prepared.policy.risk == RiskClass.YELLOW or not prepared.policy.allowed_to_execute:
            return CycleOutcome("awaiting_owner", prepared.policy.reason)
        if self.stop.stop_requested():
            return CycleOutcome("stopped", "authoritative STOP requested")
        expires = (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat()
        auth = issue_authorization(proposal, RiskClass.GREEN, expires, self.secret)
        evidence = self.executor.execute(ExecutionRequest(proposal, auth))
        if self.stop.stop_requested():
            return CycleOutcome("stopped", "STOP requested before evidence commit", evidence)
        if evidence.verdict != "indeterminate":
            return CycleOutcome("blocked", "dry-run executor returned unexpected verdict", evidence)
        checked = self.engine.apply_evidence(
            proposal, evidence, required_type="execution",
            expected_source_revision=self.source_revision,
            next_action_on_pass="await next task",
            next_action_on_fail="await qualified executor",
        )
        if not checked.verification.accepted:
            return CycleOutcome("blocked", checked.verification.reason, evidence)
        return CycleOutcome("dry_run", "no operation executed; qualification still required", evidence)
