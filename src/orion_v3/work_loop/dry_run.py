"""Read-only/dry-run executor used before sandbox qualification."""

from __future__ import annotations

from .authorization import verify_authorization
from .contracts import EvidenceRecord
from .executor import ExecutionRequest


class DryRunExecutor:
    def __init__(self, *, secret: bytes, source_revision: str):
        self._secret = secret
        self._source_revision = source_revision

    def execute(self, request: ExecutionRequest) -> EvidenceRecord:
        if not verify_authorization(request.authorization, request.proposal, self._secret):
            return EvidenceRecord(
                request.proposal.project_id,
                request.proposal.task_id,
                request.proposal.proposal_hash,
                "execution",
                "fail",
                "orion-work-loop-dry-run",
                self._source_revision,
                "authorization rejected; no operation executed",
            )
        return EvidenceRecord(
            request.proposal.project_id,
            request.proposal.task_id,
            request.proposal.proposal_hash,
            "execution",
            "indeterminate",
            "orion-work-loop-dry-run",
            self._source_revision,
            "DRY RUN ONLY; proposal authorized but no filesystem/process action executed",
        )
