from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
PARENT = HERE.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from modules.memory_historical_query import MemoryHistoricalQuery, is_historical_query


class FakeCandidates:
    def list(self):
        return {
            "candidates": [
                {
                    "candidate_id": "cand-light",
                    "source_conversation_id": "chat-light",
                    "source_message_id": "msg-light",
                },
                {
                    "candidate_id": "cand-dark",
                    "source_conversation_id": "chat-dark",
                    "source_message_id": "msg-dark",
                },
            ]
        }


class FakeReview:
    def __init__(self):
        self.candidates = FakeCandidates()

    def list_canonical(self, include_revoked=False):
        rows = [
            {
                "memory_id": "cm-light",
                "candidate_id": "cand-light",
                "content": "I prefer light mode in Orion",
                "content_sha256": "hash-light",
                "owner_scope": "owner:primary",
                "project_id": "",
                "trust_tier": "owner_message_unverified",
                "source_ref": "chat_history://chat-light:msg-light",
                "promoted_decision_id": "decision-light",
                "promoted_event_hash": "event-light",
                "active": True,
                "status": "active",
            },
            {
                "memory_id": "cm-dark",
                "candidate_id": "cand-dark",
                "content": "I prefer dark mode for ORION.",
                "content_sha256": "hash-dark",
                "owner_scope": "owner:primary",
                "project_id": "",
                "trust_tier": "owner_message_unverified",
                "source_ref": "chat_history://chat-dark:msg-dark",
                "promoted_decision_id": "decision-dark",
                "promoted_event_hash": "event-dark",
                "active": True,
                "status": "active",
            },
        ]
        return {
            "all_memories": rows,
            "memories": rows,
            "count": len(rows),
        }


class FakeFoundation:
    def __init__(self):
        self.calls = []

    def retrieve(self, query, **kwargs):
        self.calls.append((query, kwargs))
        return {
            "items": [
                {
                    "memory_id": "cm-dark",
                    "content": "I prefer dark mode for ORION.",
                    "status": "current",
                    "project_id": "",
                    "authority": "context_only",
                }
            ],
            "trace": {"include_historical": False},
        }

    def supersessions(self):
        return {
            "events": [
                {
                    "supersession_id": "sup-1",
                    "prior_memory_id": "cm-light",
                    "replacement_memory_id": "cm-dark",
                    "project_id": "",
                    "event_hash": "sup-event-1",
                }
            ]
        }


def main() -> int:
    assert is_historical_query("What did I previously prefer before dark mode?")
    assert is_historical_query("What was my earlier preference?")
    assert not is_historical_query("What mode do I prefer for ORION?")

    foundation = FakeFoundation()
    module = MemoryHistoricalQuery(FakeReview(), foundation)

    current = module.retrieve("What mode do I prefer for ORION?")
    assert current["historical_intent"] is False
    assert current["history_count"] == 0
    assert foundation.calls == []

    result = module.retrieve(
        "What did I previously prefer before dark mode?",
        project_id="",
        conversation_id="current-chat",
    )
    assert result["historical_intent"] is True
    assert len(result["current"]) == 1
    assert result["current"][0]["memory_id"] == "cm-dark"
    assert result["history_count"] == 1

    old = result["history"][0]
    assert old["memory_id"] == "cm-light"
    assert old["content"] == "I prefer light mode in Orion"
    assert old["status"] == "historical"
    assert old["superseded_by"] == "cm-dark"
    assert old["depth"] == 1
    assert old["provenance"]["source_conversation_id"] == "chat-light"
    assert old["provenance"]["source_message_id"] == "msg-light"
    assert old["provenance"]["supersession_id"] == "sup-1"
    assert old["authority"] == "context_only"

    assert foundation.calls[-1][1]["include_historical"] is False
    assert result["canonical_rows_mutated"] is False

    print("ORION_MEMORY_HISTORICAL_QUERY_V1> PASS")
    print("CURRENT_ANCHOR> DARK_MODE")
    print("HISTORICAL_EXPANSION> LIGHT_MODE")
    print("SUPERSESSION_PROVENANCE> PRESERVED")
    print("CANONICAL_ROWS_MUTATED> NONE")
    print("AUTHORITY> CONTEXT_ONLY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
