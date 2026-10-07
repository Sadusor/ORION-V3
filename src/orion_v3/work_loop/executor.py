"""Execution boundary contract for a confined Work Hand.

No concrete executor is enabled until Windows workspace confinement physically
passes.  This prevents the staged foundation from becoming an unqualified
autonomous writer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .authorization import Authorization
from .contracts import EvidenceRecord, Proposal


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    proposal: Proposal
    authorization: Authorization


class WorkHandExecutor(Protocol):
    def execute(self, request: ExecutionRequest) -> EvidenceRecord:
        """Execute only after ORION authorization inside a qualified sandbox."""
        ...
