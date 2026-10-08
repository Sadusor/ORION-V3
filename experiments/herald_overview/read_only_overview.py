"""ORION V3 experimental read-only project overview.

Design donor: Herald-OS apps/desktop/electron/context/snapshot.ts (MIT).
Reimplemented for Windows-friendly Python; no Herald/Hermes runtime dependency.
No filesystem content reads, no shell, no process launches beyond fixed git argv.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
import os
import subprocess
import time

MAX_PROJECTS = 8
MAX_CANDIDATES = 60
MAX_CHANGED = 20
TIMEOUT_SECONDS = 2.0

@dataclass(frozen=True)
class Project:
    name: str
    path: str
    changed_count: int
    changed_preview: tuple[str, ...]
    git_available: bool
    last_modified: float

def _git_status(project: Path) -> tuple[int, tuple[str, ...], bool]:
    if not (project / ".git").exists():
        return 0, (), False
    try:
        result = subprocess.run(
            ["git", "--no-optional-locks", "-C", str(project), "status",
             "--porcelain=v1", "--untracked-files=no"],
            capture_output=True, text=True, timeout=TIMEOUT_SECONDS,
            check=False, shell=False,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0",
                 "GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_NOSYSTEM": "1"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0, (), False
    if result.returncode != 0:
        return 0, (), False
    rows = result.stdout.splitlines()
    return len(rows), tuple(row[3:] for row in rows[:MAX_CHANGED]), True

def snapshot(roots: list[Path], *, max_projects: int = MAX_PROJECTS) -> dict:
    """Explicit opt-in roots only; bounded, metadata-only, no recursive traversal."""
    candidates: dict[str, tuple[Path, float]] = {}
    for root in roots:
        if not root.is_dir() or root.is_symlink():
            continue
        try:
            for child in root.iterdir():
                if len(candidates) >= MAX_CANDIDATES:
                    break
                if child.name.startswith(".") or child.is_symlink() or not child.is_dir():
                    continue
                try:
                    stamp = child.stat().st_mtime
                except OSError:
                    continue
                candidates[str(child.resolve())] = (child, stamp)
        except OSError:
            continue
    selected = sorted(candidates.values(), key=lambda item: item[1], reverse=True)[:max(0, min(max_projects, MAX_PROJECTS))]
    projects = []
    for project, stamp in selected:
        count, preview, available = _git_status(project)
        projects.append(asdict(Project(project.name, str(project), count, preview, available, stamp)))
    return {"schema": "orion.overview.v0", "observed_at": time.time(),
            "source": "explicit_read_only_roots", "projects": projects,
            "execution_enabled": False}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, action="append", required=True,
                        help="Explicit project-parent directory; repeatable")
    args = parser.parse_args()
    print(json.dumps(snapshot(args.root), indent=2))
