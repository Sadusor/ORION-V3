"""Conversation Verifier V2: advisory-only semantics, strict action boundaries.

Never changes deterministic preflight, execution authorization, STOP, or canonical state.
"""
from __future__ import annotations

from .conversation_verifier_v1 import ConversationVerifierV1, is_information_only


class ConversationVerifierV2(ConversationVerifierV1):
    def verify(self, goal: str, reply: str, model: str) -> dict:
        # V1 owns the deterministic preflight and all strict routing.
        result = super().verify(goal, reply, model)
        if not is_information_only(goal):
            return result
        if result.get("preflight") != "pass":
            return result
        # An informational reply cannot be marked execution-verified.
        # A reviewer's ambiguous "ready=false" with no identified issues is
        # not proof of a false claim. Preserve an explicit uncertainty marker.
        if (
            result.get("quality_state") == "pass"
            and not result.get("unsupported_claims")
            and not result.get("missing_evidence")
            and str(result.get("quality_reason", "")).startswith(
                "UNVERIFIED CONVERSATIONAL CLAIMS"
            )
        ):
            amended = dict(result)
            amended["quality_reason"] = (
                "CONVERSATIONAL REVIEW INCONCLUSIVE — no specific unsupported "
                "claim or missing evidence identified. This is not execution "
                "verification. " + amended["quality_reason"]
            )
            amended["needs_escalation"] = True
            return amended
        return result
