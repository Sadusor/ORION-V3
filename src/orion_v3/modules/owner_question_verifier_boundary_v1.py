"""Additive verifier boundary: classify and review owner text, not retrieved sources.

Deterministic preflight remains unchanged and always runs on the complete reply.
Only exact known prompt envelopes are recognized. No execution authorization.
"""
from __future__ import annotations
import re
from .verifier_reliability_v1 import VerifierReliabilityV1

_OWNER = re.compile(r"<OWNER_CURRENT_MESSAGE>\s*(.*?)\s*</OWNER_CURRENT_MESSAGE>",re.S)
_SOURCE = re.compile(r"\n\n<ORION_INDEXED_(?:SOURCES|DOCUMENTS)\b",re.I)
_TAG = re.compile(r"</?ORION_INDEXED_(?:SOURCES|DOCUMENTS)\b",re.I)

def owner_question_for_review(goal: str) -> str:
    raw=str(goal or "")
    matches=list(_OWNER.finditer(raw))
    if len(matches)==1:
        raw=matches[0].group(1)
    # Source blocks can be appended to the owner's question by the retrieval
    # wrapper before canonical memory composition. Never classify their code.
    marker=_SOURCE.search(raw)
    if marker:
        raw=raw[:marker.start()]
    return raw.strip()

class OwnerQuestionVerifierBoundaryV1:
    def __init__(self, underlying=None):
        self.underlying=underlying or VerifierReliabilityV1()
    def deterministic_preflight(self, reply: str):
        return self.underlying.deterministic_preflight(reply)
    def verify(self, goal: str, reply: str, model: str):
        # Strict reply safety is still enforced by the underlying verifier.
        return self.underlying.verify(owner_question_for_review(goal),reply,model)
