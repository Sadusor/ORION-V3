"""Cloud-model bridge for ORION Work Loop.

This module accepts already-connected provider callbacks by dependency injection.
It neither stores credentials nor makes network requests nor executes actions.
Provider output is untrusted until canonical Vault identity and policy validation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .engine import WorkLoopEngine
from .qwen_proposal_adapter import parse_qwen_proposal
from .contracts import Proposal

MAX_BRIEF_CHARS = 4096


@dataclass(frozen=True, slots=True)
class CloudSuggestion:
    provider: str
    proposal: Proposal


def request_cloud_proposal(*, provider: str, invoke: Callable[[str], str],
                           engine: WorkLoopEngine, task_brief: str) -> CloudSuggestion:
    if not isinstance(provider, str) or not provider.strip() or len(provider) > 80:
        raise ValueError("provider identity required")
    if not isinstance(task_brief, str) or not task_brief.strip() or len(task_brief) > MAX_BRIEF_CHARS:
        raise ValueError("bounded task brief required")
    if not callable(invoke):
        raise ValueError("provider must be an injected callable")
    state = engine.vault.load()
    prompt = (
        "Return exactly one JSON object matching ORION Proposal fields: "
        "project_id, task_id, operation, workspace, args, requested_network, "
        "requested_install, requested_system_change. All requested_* fields "
        "must be false. No markdown, tool calls, secrets, or execution claims. "
        "This is an advisory proposal only. ORION alone authorizes actions.\n"
        f"Canonical project_id: {state.project_id}\n"
        f"Canonical task_id: {state.current_task}\n"
        f"Task: {task_brief}"
    )
    raw = invoke(prompt)
    return CloudSuggestion(provider=provider.strip(), proposal=parse_qwen_proposal(raw, engine))


def review_cloud_proposal(*, provider: str, invoke: Callable[[str], str],
                          proposal: Proposal) -> str:
    """Review is advisory only: cannot grant authorization or claim verified PASS."""
    if not provider or not callable(invoke):
        raise ValueError("reviewer missing")
    brief = ("Review the following untrusted proposed operation for correctness and "
             "security. Reply with critique only. Do not claim execution or PASS.\n"
             + proposal.canonical_payload().decode("utf-8"))
    result = invoke(brief)
    if not isinstance(result, str) or len(result.encode("utf-8")) > 8192:
        raise ValueError("review exceeds bound")
    return result
