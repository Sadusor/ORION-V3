"""Small owner-instruction hook for future Work Chat integration.

The core loop asks an adapter for the newest instruction at cycle boundaries.
No file-based chat system is introduced here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class OwnerInstruction:
    instruction_id: str
    text: str


class OwnerInstructionSource(Protocol):
    def poll(self, *, after_id: str | None = None) -> OwnerInstruction | None:
        """Return a newer instruction, or None when there is no owner update."""
        ...
