"""Anthropic SRT configuration adapter for a future physical Windows spike.

This module ONLY builds/validates configuration.  It deliberately does not
install SRT, mutate ACLs, spawn processes, or claim the sandbox is qualified.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .paths import resolved_workspace


@dataclass(frozen=True, slots=True)
class SrtSandboxPlan:
    workspace: str
    allowed_domains: tuple[str, ...] = ()
    deny_read: tuple[str, ...] = ()
    deny_write: tuple[str, ...] = ()

    def as_config(self) -> dict[str, Any]:
        root = str(resolved_workspace(self.workspace))
        return {
            "network": {
                "allowedDomains": list(self.allowed_domains),
                "deniedDomains": [],
                "allowLocalBinding": False,
            },
            "filesystem": {
                "denyRead": list(self.deny_read),
                "allowRead": [root],
                "allowWrite": [root],
                "denyWrite": list(self.deny_write),
                "allowGitConfig": False,
            },
        }


def work_hand_plan(
    workspace: str | Path,
    *,
    network_domains: tuple[str, ...] = (),
    extra_deny_read: tuple[str, ...] = (),
    extra_deny_write: tuple[str, ...] = (),
) -> SrtSandboxPlan:
    root = resolved_workspace(workspace)
    # Defense in depth. SRT itself also has mandatory deny paths; ORION keeps
    # these explicit so policy is visible and testable on our side.
    deny_write = (
        str(root / ".git" / "hooks"),
        str(root / ".git" / "config"),
        str(root / ".mcp.json"),
        *extra_deny_write,
    )
    return SrtSandboxPlan(
        workspace=str(root),
        allowed_domains=tuple(network_domains),
        deny_read=tuple(extra_deny_read),
        deny_write=tuple(deny_write),
    )
