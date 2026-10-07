"""Fail-closed workspace path checks.

These checks are pre-execution policy checks.  They are NOT a replacement for
OS-enforced sandboxing.  The physical sandbox gate remains mandatory.
"""

from __future__ import annotations

from pathlib import Path


class WorkspaceViolation(ValueError):
    pass


def resolved_workspace(path: str | Path) -> Path:
    root = Path(path).expanduser().resolve(strict=False)
    if not root.is_absolute():
        raise WorkspaceViolation("workspace must resolve to an absolute path")
    return root


def require_inside_workspace(candidate: str | Path, workspace: str | Path) -> Path:
    root = resolved_workspace(workspace)
    raw = Path(candidate).expanduser()
    target = raw if raw.is_absolute() else root / raw
    target = target.resolve(strict=False)
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise WorkspaceViolation(f"path escapes workspace: {candidate}") from exc
    return target


def overlaps_frozen_path(
    candidate: str | Path, workspace: str | Path, frozen_paths: list[str]
) -> bool:
    target = require_inside_workspace(candidate, workspace)
    for frozen in frozen_paths:
        protected = require_inside_workspace(frozen, workspace)
        if target == protected or protected in target.parents or target in protected.parents:
            return True
    return False
