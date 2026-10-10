"""Conversation-only uncertainty handling; never grants execution or tool authority.

Deterministic preflight remains mandatory. For an ordinary informational question,
a semantic reviewer may mark uncertain claims for disclosure rather than suppressing
the entire response. Executable requests keep the existing strict verifier.
"""
from __future__ import annotations
import re
from .verifier_preflight import VerifierPreflightModule

_ACTION = re.compile(
    r"(?i)\b(?:execute|run|launch|install|delete|deploy|write|modify|commit|"
    r"push|pull|merge|checkout|approve|authorize|stop|start|powershell|"
    r"terminal|shell|script|command)\b"
)

def is_information_only(goal: str) -> bool:
    """Conservative routing: ambiguous/action-bearing requests use strict review."""
    value = str(goal or "").strip()
    return bool(value) and not _ACTION.search(value)

class ConversationVerifierV1:
    """Adapter, not a replacement for deterministic ORION execution gates."""

    def __init__(self, strict: VerifierPreflightModule | None = None):
        self.strict = strict or VerifierPreflightModule()

    def verify(self, goal: str, reply: str, model: str) -> dict:
        # Always enforce the same deterministic executable/action-claim safety check.
        preflight = self.strict.deterministic_preflight(reply)
        if not preflight["allowed"]:
            return {
                "preflight": "blocked",
                "preflight_reason": preflight["reason"],
                "quality_state": "not-run",
                "quality_reason": "",
                "unsupported_claims": [],
                "missing_evidence": [],
                "needs_escalation": False,
            }
        # Strict semantics for all work/authority/execution-related conversations.
        result = self.strict.verify(goal, reply, model)
        if not is_information_only(goal):
            return result
        # Non-executable informational chat may disclose semantic uncertainty.
        # A verifier transport/schema failure still fails closed upstream.
        if result["preflight"] == "pass" and result["quality_state"] == "blocked":
            result = dict(result)
            result["quality_state"] = "pass"
            result["quality_reason"] = (
                "UNVERIFIED CONVERSATIONAL CLAIMS — review source evidence. "
                + result["quality_reason"]
            )
            result["needs_escalation"] = True
        return result
