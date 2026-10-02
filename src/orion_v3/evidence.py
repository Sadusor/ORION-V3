from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class Outcome(str, Enum):
    CONFIRMED = "confirmed"
    UNVERIFIABLE = "unverifiable"
    REFUSED = "refused"
    FAILED = "failed"
    STOPPED = "stopped"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class EvidenceEnvelope:
    """ORION-owned normalized evidence.

    Donor/model prose is never itself proof of a side effect.
    """

    task_id: str
    lease_id: str
    operation_id: str
    implementation_id: str
    outcome: Outcome
    result: Mapping[str, Any] = field(default_factory=dict)
    verifier: str = ""
    error: str | None = None