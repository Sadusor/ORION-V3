"""Post-memory, opt-in read-only Gitea search for the EXISTING ORION Qwen chat.

Owner text goes through frozen canonical memory unchanged. This wrapper attaches
bounded untrusted code context only after the final memory prompt is composed.
"""
from __future__ import annotations
from contextlib import contextmanager
from contextvars import ContextVar
from .streaming_brain_pipeline import StreamingBrainPipeline
from .gitea_search_service_v1 import search_live_gitea
from .gitea_search_context_v1 import render_untrusted_code_context
from .gitea_brain_adapter_v1 import OPERATING_GUIDANCE
from .orion_project_context_v1 import is_orion_project_question, project_status_context, render_project_status_context

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

class GiteaChatStreamingBrain(StreamingBrainPipeline):
    """Preserves StreamingBrainPipeline verifier and the original Local Brain."""

    def start(self, goal: str, model: str = "") -> dict:
        request = _requested.get()
        if request is not None:
            query,state_dir = request
            try:
                if is_orion_project_question(query):
                    checkpoint = project_status_context()
                    goal += "\n\n" + render_project_status_context(checkpoint)
                    return super().start(goal, model)
                context = search_live_gitea(query=query,project_id="orion-v3",
                                           state_dir=state_dir)
                if context["results"]:
                    goal += ("\n\n" + render_untrusted_code_context(context)
                             + "\n" + OPERATING_GUIDANCE)
                else:
                    goal += "\n\nGitea code search returned no matches; do not claim repository access was successful."
            except (ValueError, PermissionError, OSError, ConnectionError):
                goal += "\n\nGitea repository search unavailable; explicitly disclose this limitation. Do not invent file references."
        return super().start(goal,model)
