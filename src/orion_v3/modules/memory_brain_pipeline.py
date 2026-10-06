from __future__ import annotations

import copy
import threading
from typing import Any

from .memory_retrieval import MemoryRetrievalModule
from .streaming_brain_pipeline import StreamingBrainPipeline


class MemoryAwareBrainPipeline:
    """Compose read-only retrieval in front of the frozen streaming brain pipeline.

    Memory is supplied as context only. The wrapped Local Brain/verifier modules
    remain unchanged and keep all of their existing authority boundaries.
    """

    def __init__(
        self,
        brain: StreamingBrainPipeline,
        memory: MemoryRetrievalModule,
    ):
        self.brain = brain
        self.local_brain = brain.local_brain
        self.memory = memory
        self._lock = threading.RLock()
        self._session: dict[str, Any] = {
            "brain_started_utc": "",
            "owner_goal": "",
            "memory": self._blank_memory("idle"),
        }

    @staticmethod
    def _blank_memory(state: str, error: str = "") -> dict[str, Any]:
        return {
            "schema": "orion.memory-brief/1",
            "state": state,
            "authority": "context_only",
            "query": "",
            "count": 0,
            "items": [],
            "trace": {},
            "error": error,
        }

    def cached_models(self) -> list[str]:
        return self.brain.cached_models()

    def default_model(self) -> str:
        return self.brain.default_model()

    def start(
        self,
        goal: str,
        model: str = "",
        *,
        memory_query: str = "",
        conversation_id: str = "",
        project_id: str | None = None,
    ) -> dict:
        owner_goal = str(goal or "").strip()
        query = str(memory_query or owner_goal).strip()

        try:
            retrieval = self.memory.retrieve(
                query,
                conversation_id=conversation_id,
                project_id=project_id,
            )
            composed = self.memory.compose_owner_request(owner_goal, retrieval)
            brief = {
                "schema": "orion.memory-brief/1",
                "state": "pass" if retrieval.get("items") else "empty",
                "authority": "context_only",
                "query": retrieval.get("query", ""),
                "count": len(retrieval.get("items", [])),
                "items": [
                    {
                        "id": item.get("id", ""),
                        "title": item.get("title", ""),
                        "preview": item.get("preview", ""),
                        "score": item.get("score", 0.0),
                        "layer": item.get("layer", "L1"),
                        "provenance": copy.deepcopy(item.get("provenance", {})),
                    }
                    for item in retrieval.get("items", [])
                ],
                "trace": copy.deepcopy(retrieval.get("trace", {})),
                "error": "",
            }
        except Exception as exc:
            # Retrieval is advisory context, not an authority/security gate.
            # A retrieval failure must be visible but must not falsely make the
            # assistant unavailable when the frozen brain itself is healthy.
            composed = owner_goal
            brief = self._blank_memory("error", str(exc).strip() or exc.__class__.__name__)
            brief["query"] = query

        started = self.brain.start(composed, model)
        stamp = str(started.get("brain_started_utc") or "")
        with self._lock:
            self._session = {
                "brain_started_utc": stamp,
                "owner_goal": owner_goal,
                "memory": brief,
            }
        return self.view()

    def view(self) -> dict:
        base = self.brain.view()
        stamp = str(base.get("brain_started_utc") or "")
        with self._lock:
            session = copy.deepcopy(self._session)

        if stamp and stamp == session.get("brain_started_utc"):
            # Never let the deterministic retrieval wrapper rewrite what the UI
            # reports as the owner's actual request.
            base["goal"] = session.get("owner_goal", "")
            base["brain_memory"] = session.get("memory", self._blank_memory("idle"))
        else:
            base["brain_memory"] = self._blank_memory("idle")
        return base
