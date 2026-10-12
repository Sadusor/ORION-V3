"""Forge-to-ORION read-only workspace projection (V1 candidate).

This module never executes code, writes files, grants approval, or calls models.
The caller must supply records from authenticated ORION sources; UI data is
not an authorization token. Frozen session and policy modules are untouched.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True, slots=True)
class WorkspaceTask:
    task_id: str
    project_id: str
    title: str
    status: str
    coder: str | None = None
    reviewer: str | None = None
    verified_result: str | None = None
    pending_approval: bool = False


_ALLOWED = frozenset({"queued", "coding", "review", "awaiting_approval", "blocked", "verified", "failed"})


def project_workspace_view(
    project_id: str,
    tasks: Iterable[WorkspaceTask],
    *,
    current_revision: str,
    source_authenticated: bool,
) -> dict:
    """Produce unprivileged Forge/phone display data from trusted task records.

    Fail closed when the caller cannot attest to the source. Status is never
    inferred from a model's message or a browser-side approval click.
    """
    if not source_authenticated:
        raise ValueError("authenticated canonical source required")
    if not project_id or not current_revision:
        raise ValueError("project and source revision required")
    entries = []
    seen = set()
    for t in tasks:
        if not isinstance(t, WorkspaceTask) or t.project_id != project_id:
            raise ValueError("invalid or cross-project task")
        if not t.task_id or t.task_id in seen or t.status not in _ALLOWED:
            raise ValueError("invalid task identity or status")
        seen.add(t.task_id)
        if t.pending_approval != (t.status == "awaiting_approval"):
            raise ValueError("approval state mismatch")
        entries.append({
            "task_id": t.task_id,
            "title": t.title,
            "status": t.status,
            "coder": t.coder,
            "reviewer": t.reviewer,
            "verified_result": t.verified_result,
            "pending_approval": t.pending_approval,
        })
    return {
        "schema": "orion.forge.workspace.v1",
        "project_id": project_id,
        "source_revision": current_revision,
        "read_only": True,
        "can_execute": False,
        "can_approve": False,
        "tasks": entries,
        "pending_approval_count": sum(x["pending_approval"] for x in entries),
    }
