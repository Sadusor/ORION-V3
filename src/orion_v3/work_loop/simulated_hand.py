"""Independent simulated Work Hand: never performs real I/O.

Strictly validates exact authorization and models a bounded operation.
The coordinator still treats all simulated evidence as indeterminate.
"""
from __future__ import annotations

from .authorization import verify_authorization
from .contracts import EvidenceRecord
from .executor import ExecutionRequest
from .nonce_store import NonceStore


class SimulatedWorkHand:
    def __init__(self, *, secret: bytes, source_revision: str, nonce_store: NonceStore | None = None):
        self._secret = secret
        self._revision = source_revision
        self._nonce_store = nonce_store

    def execute(self, request: ExecutionRequest) -> EvidenceRecord:
        p = request.proposal
        authorized = verify_authorization(request.authorization, p, self._secret)
        if authorized and self._nonce_store is not None:
            authorized = self._nonce_store.consume(request.authorization.nonce)
        return EvidenceRecord(
            p.project_id, p.task_id, p.proposal_hash, "execution",
            "indeterminate" if authorized else "fail",
            "orion-simulated-work-hand", self._revision,
            "SIMULATION ONLY: no source file, process, or network operation executed"
            if authorized else "authorization rejected; nothing executed",
        )
