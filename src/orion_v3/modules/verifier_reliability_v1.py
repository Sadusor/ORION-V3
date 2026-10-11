"""Bounded verifier retry adapter. No authority changes and never fails open."""
from __future__ import annotations

from .conversation_verifier_v2 import ConversationVerifierV2
from .verifier_preflight import VerifierError


class VerifierReliabilityV1:
    def __init__(self, underlying=None):
        self.underlying = underlying or ConversationVerifierV2()

    def deterministic_preflight(self, reply: str) -> dict:
        return self.underlying.strict.deterministic_preflight(reply)

    def verify(self, goal: str, reply: str, model: str) -> dict:
        # Retry once ONLY for malformed schema payload; never retry permissions,
        # preflight denial, transport error, or semantic rejection.
        try:
            return self.underlying.verify(goal, reply, model)
        except VerifierError as exc:
            if "malformed structured JSON" not in str(exc) and "did not match the required schema" not in str(exc):
                raise
        return self.underlying.verify(goal, reply, model)
