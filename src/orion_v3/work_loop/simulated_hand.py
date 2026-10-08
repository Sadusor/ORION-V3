"""Independent simulated Work Hand: never performs real I/O.

Strictly validates exact authorization and models a bounded operation.
The coordinator still treats all simulated evidence as indeterminate.
"""
from __future__ import annotations

from .authorization import verify_authorization
from .contracts import EvidenceRecord
from .executor import ExecutionRequest


class SimulatedWorkHand:
    def __init__(self, *, secret: bytes, source_revision: str):
        self._secret = secret
        self._revision = source_revision

    def execute(self, request: ExecutionRequest) -> EvidenceRecord:
        p = request.proposal
        authorized = verify_authorization(request.authorization, p, self._secret)
        return EvidenceRecord(
            p.project_id, p.task_id, p.proposal_hash, "execution",
            "indeterminate" if authorized else "fail",
            "orion-simulated-work-hand", self._revision,
            "SIMULATION ONLY: no source file, process, or network operation executed"
            if authorized else "authorization rejected; nothing executed",
        )
