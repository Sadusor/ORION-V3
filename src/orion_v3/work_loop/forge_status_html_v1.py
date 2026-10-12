"""Forge read-only HTML view adapter V1 candidate.

Accepts only a validated workspace projection. Produces a static HTML view:
no scripts, forms, network requests, inline events, previews, or file APIs.
This is a safe integration seam, not deployment of the supplied Forge app.
"""
from __future__ import annotations

from html import escape


def render_forge_status_html(view: dict) -> str:
    if not isinstance(view, dict) or view.get("schema") != "orion.forge.workspace.v1":
        raise ValueError("unsupported workspace schema")
    if view.get("read_only") is not True or view.get("can_execute") is not False or view.get("can_approve") is not False:
        raise ValueError("workspace authority mismatch")
    if not isinstance(view.get("project_id"), str) or not view["project_id"]:
        raise ValueError("project identity missing")
    if not isinstance(view.get("source_revision"), str) or not view["source_revision"]:
        raise ValueError("source revision missing")
    tasks = view.get("tasks")
    if not isinstance(tasks, list) or len(tasks) > 1000:
        raise ValueError("invalid task list")
    statuses = {"queued", "coding", "review", "awaiting_approval", "blocked", "verified", "failed"}
    seen = set()
    cards = []
    approvals = 0
    for t in tasks:
        if not isinstance(t, dict) or not isinstance(t.get("task_id"), str) or not t["task_id"] or t["task_id"] in seen:
            raise ValueError("invalid task identity")
        seen.add(t["task_id"])
        if t.get("status") not in statuses or not isinstance(t.get("title"), str):
            raise ValueError("invalid task")
        if type(t.get("pending_approval")) is not bool or t["pending_approval"] != (t["status"] == "awaiting_approval"):
            raise ValueError("approval mismatch")
        for k in ("coder", "reviewer", "verified_result"):
            if t.get(k) is not None and not isinstance(t[k], str):
                raise ValueError("invalid task detail")
        approvals += int(t["pending_approval"])
        def field(k: str) -> str:
            return escape(t.get(k) or "—", quote=True)
        cards.append(
            '<article class="task"><h3>' + field("title") + '</h3>'
            '<p class="state">' + field("status") + '</p>'
            '<p>Coder: ' + field("coder") + ' · Reviewer: ' + field("reviewer") + '</p>'
            '<p>Verification: ' + field("verified_result") + '</p></article>'
        )
    if type(view.get("pending_approval_count")) is not int or view["pending_approval_count"] != approvals:
        raise ValueError("approval count mismatch")
    project = escape(view["project_id"], quote=True)
    revision = escape(view["source_revision"], quote=True)
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>ORION Forge — status</title>'
        '<style>body{margin:0;background:#0d1117;color:#e6edf3;font:14px system-ui}'
        'main{max-width:1100px;margin:auto;padding:24px}.layout{display:grid;grid-template-columns:240px 1fr;gap:18px}'
        'aside,.task{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px}'
        '.task{margin:0 0 12px}.state{color:#79c0ff}small{color:#8b949e}'
        '@media(max-width:650px){.layout{grid-template-columns:1fr}}</style></head>'
        '<body><main><h1>ORION · Forge</h1><small>Read-only project status · no execution</small>'
        '<div class="layout"><aside><h2>Project</h2><p>' + project + '</p>'
        '<small>Revision: ' + revision + '</small><p>Pending approvals: ' + str(approvals) + '</p>'
        '<p>Approval and STOP remain in ORION.</p></aside>'
        '<section aria-label="Task status"><h2>Tasks</h2>' + (''.join(cards) or '<p>No tasks reported.</p>') +
        '</section></div></main></body></html>'
    )
