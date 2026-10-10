"""Conversation Verifier V2: advisory-only semantics, strict action boundaries.

Never changes deterministic preflight, execution authorization, STOP, or canonical state.
"""
from __future__ import annotations

import re
from .conversation_verifier_v1 import ConversationVerifierV1, is_information_only

_EXPLAIN = re.compile(r'(?i)^\s*(?:what|why|how|explain|describe|compare|tell me about|τι|πώς|πως|γιατί|εξήγησε)\b')
_REQUEST = re.compile(r'(?i)\b(?:can you|could you|please|i want you to|θα μπορούσες|μπορείς να)\s+(?:run|execute|start|stop|install|delete|write|modify|commit|push|pull|merge|deploy|approve|authorize|τρέξεις|εκτελέσεις|διαγράψεις|γράψεις)\b')


def is_explanatory_question(goal: str) -> bool:
    return bool(_EXPLAIN.search(goal or '')) and not bool(_REQUEST.search(goal or ''))


class ConversationVerifierV2(ConversationVerifierV1):
    def verify(self, goal: str, reply: str, model: str) -> dict:
        # V1 owns the deterministic preflight and all strict routing.
        informational = is_information_only(goal) or is_explanatory_question(goal)
        if informational and not is_information_only(goal):
            gate = self.strict.deterministic_preflight(reply)
            if not gate['allowed']:
                return {'preflight':'blocked', 'preflight_reason':gate['reason'], 'quality_state':'not-run', 'quality_reason':'', 'unsupported_claims':[], 'missing_evidence':[], 'needs_escalation':False}
            result = self.strict.verify(goal, reply, model)
            if result.get('preflight') == 'pass' and result.get('quality_state') == 'blocked':
                result = dict(result)
                result['quality_state'] = 'pass'
                result['quality_reason'] = 'UNVERIFIED CONVERSATIONAL CLAIMS — ' + result.get('quality_reason','')
                result['needs_escalation'] = True
        else:
            result = super().verify(goal, reply, model)
        if not informational:
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
