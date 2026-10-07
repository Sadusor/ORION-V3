from __future__ import annotations

import copy
import re
from typing import Any

SCHEMA = "orion.memory-historical-query/1"

_HISTORICAL_INTENT_RE = re.compile(
    r"\b(previously|previous|before|earlier|historical|history|prior|used\s+to)\b",
    re.I,
)


def is_historical_query(query: str) -> bool:
    return bool(_HISTORICAL_INTENT_RE.search(str(query or "")))


class MemoryHistoricalQuery:
    """Read-only expansion of current durable memories into superseded history.

    This module never changes canonical rows, decisions, or supersession events.
    It starts from the already-proven current durable retrieval result, then
    follows the append-only supersession ledger backwards to prior evidence.
    """

    def __init__(self, review: Any, foundation: Any):
        self.review = review
        self.foundation = foundation

    def _memory_map(self) -> dict[str, dict[str, Any]]:
        listed = self.review.list_canonical(include_revoked=True)
        return {
            str(x.get("memory_id") or ""): copy.deepcopy(x)
            for x in listed.get("all_memories", [])
            if isinstance(x, dict) and str(x.get("memory_id") or "")
        }

    def _candidate_map(self) -> dict[str, dict[str, Any]]:
        queue = getattr(self.review, "candidates", None)
        if queue is None or not hasattr(queue, "list"):
            return {}
        listed = queue.list()
        return {
            str(x.get("candidate_id") or ""): copy.deepcopy(x)
            for x in listed.get("candidates", [])
            if isinstance(x, dict) and str(x.get("candidate_id") or "")
        }

    def retrieve(
        self,
        query: str,
        *,
        project_id: str = "",
        conversation_id: str = "",
        limit: int = 6,
    ) -> dict[str, Any]:
        query = str(query or "").strip()
        if not is_historical_query(query):
            return {
                "schema": SCHEMA,
                "query": query,
                "historical_intent": False,
                "current": [],
                "history": [],
                "history_count": 0,
                "authority": "context_only",
                "canonical_rows_mutated": False,
            }

        current_result = self.foundation.retrieve(
            query,
            project_id=project_id,
            conversation_id=conversation_id,
            limit=max(1, min(int(limit or 6), 12)),
            include_historical=False,
        )
        current_items = [
            copy.deepcopy(x)
            for x in current_result.get("items", [])
            if isinstance(x, dict)
        ]

        relations = [
            x
            for x in self.foundation.supersessions().get("events", [])
            if isinstance(x, dict)
            and str(x.get("project_id") or "") == str(project_id or "")
        ]
        prior_by_replacement = {
            str(x.get("replacement_memory_id") or ""): copy.deepcopy(x)
            for x in relations
            if str(x.get("replacement_memory_id") or "")
            and str(x.get("prior_memory_id") or "")
        }

        memories = self._memory_map()
        candidates = self._candidate_map()
        history: list[dict[str, Any]] = []
        seen: set[str] = set()

        for current in current_items:
            current_id = str(current.get("memory_id") or "")
            replacement_id = current_id
            depth = 1
            while replacement_id in prior_by_replacement and len(history) < limit:
                relation = prior_by_replacement[replacement_id]
                prior_id = str(relation.get("prior_memory_id") or "")
                if not prior_id or prior_id in seen:
                    break
                seen.add(prior_id)
                memory = memories.get(prior_id)
                if not memory:
                    break
                if str(memory.get("project_id") or "") != str(project_id or ""):
                    break

                candidate = candidates.get(str(memory.get("candidate_id") or ""), {})
                history.append({
                    "memory_id": prior_id,
                    "content": str(memory.get("content") or ""),
                    "content_sha256": str(memory.get("content_sha256") or ""),
                    "status": "historical",
                    "historical_reason": "superseded",
                    "superseded_by": replacement_id,
                    "depth": depth,
                    "project_id": str(memory.get("project_id") or ""),
                    "owner_scope": str(memory.get("owner_scope") or ""),
                    "trust_tier": str(memory.get("trust_tier") or ""),
                    "provenance": {
                        "candidate_id": str(memory.get("candidate_id") or ""),
                        "source_ref": str(memory.get("source_ref") or ""),
                        "source_conversation_id": str(
                            candidate.get("source_conversation_id") or ""
                        ),
                        "source_message_id": str(
                            candidate.get("source_message_id") or ""
                        ),
                        "promotion_event_id": str(
                            memory.get("promoted_decision_id") or ""
                        ),
                        "promotion_event_hash": str(
                            memory.get("promoted_event_hash") or ""
                        ),
                        "supersession_id": str(
                            relation.get("supersession_id") or ""
                        ),
                        "supersession_event_hash": str(
                            relation.get("event_hash") or ""
                        ),
                    },
                    "authority": "context_only",
                })
                replacement_id = prior_id
                depth += 1

        return {
            "schema": SCHEMA,
            "query": query,
            "historical_intent": True,
            "current": current_items,
            "history": history,
            "history_count": len(history),
            "trace": {
                "current_anchor_count": len(current_items),
                "supersession_events_considered": len(relations),
                "history_source": "append_only_supersession_ledger",
                "canonical_rows_mutated": False,
                "authority": "context_only",
            },
            "authority": "context_only",
            "canonical_rows_mutated": False,
        }
