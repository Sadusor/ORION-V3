"""Non-executing Windows isolation preflight. Never grants execution."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import PureWindowsPath
from .stop import StopSource

@dataclass(frozen=True)
class IsolationPreflight:
    ready: bool
    reason: str

def inspect_workspace(workspace: str, stop: StopSource | None, *, platform: str) -> IsolationPreflight:
    if stop is None:
        return IsolationPreflight(False, "authoritative STOP source missing")
    try:
        if stop.stop_requested():
            return IsolationPreflight(False, "authoritative STOP requested")
    except Exception:
        return IsolationPreflight(False, "authoritative STOP unavailable")
    if platform != "win32":
        return IsolationPreflight(False, "Windows target required")
    path = PureWindowsPath(workspace)
    if not path.is_absolute() or path.drive.upper() != "E:" or ".." in path.parts:
        return IsolationPreflight(False, "disposable absolute E: workspace required")
    return IsolationPreflight(False, "OS isolation and cross-process STOP unqualified")
