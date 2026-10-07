"""STOP adapter contract.

This module does not create another STOP.  A runtime adapter must delegate to
the existing authoritative ORION STOP mechanism.
"""

from __future__ import annotations

from typing import Protocol


class StopSource(Protocol):
    def stop_requested(self) -> bool:
        """Return the current state of ORION's authoritative STOP."""
        ...
