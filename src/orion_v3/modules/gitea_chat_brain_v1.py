"""Post-memory, opt-in read-only Gitea search for the EXISTING ORION Qwen chat.

Owner text goes through frozen canonical memory unchanged. This wrapper attaches
untrusted code context only after the final memory prompt is composed.
"""
from __future__ import annotations
from contextlib import contextmanager
from contextvars import ContextVar
from .streaming_brain_pipeline import StreamingBrainPipeline
from .conversation_verifier_v2 import ConversationVerifierV2
from .gitea_auto_index_v2 import search_live_gitea_v2
from .gitea_search_context_v1 import render_untrusted_code_context
from .gitea_brain_adapter_v1 import OPERATING_GUIDANCE
from .orion_project_context_v1 import is_orion_project_question

_requested = ContextVar("orion_gitea_requested_context", default=None)

@contextmanager
def gitea_chat_request(*, project_id: str, owner_text: str, state_dir):
    if project_id != "orion-v3" or not owner_text.strip():
        yield
        return
    token = _requested.set((owner_text[:300],state_dir))
    try:
        yield
    finally:
        _requested.reset(token)

def attach_bounded_reference(goal: str, reference: str, *, max_bytes: int | None = None) -> str:
    """Include all retrieved bounded search excerpts without a second artificial cap.

    The search provider already enforces its independent, read-only source limit.
    Model runtime context limits remain in effect; this does not change memory.
    """
    if not reference.strip():
        return goal
    return goal + "\n\n" + reference


class GiteaChatStreamingBrain(StreamingBrainPipeline):
    """Keep deterministic preflight and all execution gates; adapt conversational review."""

    def __init__(self, local_brain=None, verifier=None):
        super().__init__(local_brain=local_brain, verifier=verifier or ConversationVerifierV2())

    def start(self, goal: str, model: str = "") -> dict:
        request = _requested.get()
        if request is not None:
            query,state_dir = request
            try:
                context = search_live_gitea_v2(query=query,project_id="orion-v3",
                                           state_dir=state_dir)
                if context["results"]:
                    goal = attach_bounded_reference(goal, render_untrusted_code_context(context)
                             + "\n" + OPERATING_GUIDANCE)
                else:
                    goal += "\n\nGitea code search returned no matches; do not claim repository access was successful."
            except (ValueError, PermissionError, OSError, ConnectionError):
                goal += "\n\nGitea repository search unavailable; explicitly disclose this limitation. Do not invent file references."
        return super().start(goal,model)
