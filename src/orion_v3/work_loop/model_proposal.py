"""Fail-closed, reasoning-only adapter from local model text to ORION Proposal.

No model output can authorize, execute, or assert evidence. The caller supplies
project/task/workspace from the canonical Vault, never from model text.
"""
from __future__ import annotations

import json
from .contracts import Proposal

ALLOWED_FIELDS = frozenset({"operation", "args", "requested_network", "requested_install", "requested_system_change"})


class ProposalParseError(ValueError):
    pass


def parse_model_proposal(text: str, *, project_id: str, task_id: str, workspace: str) -> Proposal:
    """Parse a single JSON proposal; authority and task scope remain caller-owned."""
    if not isinstance(text, str) or not text.strip() or len(text) > 16384:
        raise ProposalParseError("empty or oversized model proposal")
    try:
        raw = json.loads(text)
    except (ValueError, TypeError) as exc:
        raise ProposalParseError("model response must be one JSON object") from exc
    if not isinstance(raw, dict) or set(raw) - ALLOWED_FIELDS:
        raise ProposalParseError("unknown model proposal fields")
    operation = raw.get("operation")
    args = raw.get("args", {})
    if not isinstance(operation, str) or not operation.strip() or not isinstance(args, dict):
        raise ProposalParseError("invalid operation or arguments")
    for field in ("requested_network", "requested_install", "requested_system_change"):
        if not isinstance(raw.get(field, False), bool):
            raise ProposalParseError(f"{field} must be boolean")
    if not all(isinstance(x, str) and x for x in (project_id, task_id, workspace)):
        raise ProposalParseError("canonical scope is required")
    proposal = Proposal(project_id=project_id, task_id=task_id, operation=operation,
                        workspace=workspace, args=args,
                        requested_network=raw.get("requested_network", False),
                        requested_install=raw.get("requested_install", False),
                        requested_system_change=raw.get("requested_system_change", False))
    try:
        proposal.canonical_payload()
    except (ValueError, TypeError) as exc:
        raise ProposalParseError("unsupported proposal arguments") from exc
    return proposal
