from __future__ import annotations

import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
PARENT = HERE.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from modules.chat_history import ChatHistoryStore
from modules.memory_retrieval import MemoryRetrievalModule, SCHEMA, TRACE_SCHEMA


def seed(store: ChatHistoryStore) -> None:
    store.sync(
        {
            "conversations": [
                {
                    "id": "personal-old",
                    "title": "Local model choice",
                    "project_id": "",
                    "pinned": 1,
                    "archived": 0,
                    "deleted": 0,
                    "created_at_ms": 1000,
                    "updated_at_ms": 3100,
                },
                {
                    "id": "personal-greek",
                    "title": "Μνήμη",
                    "project_id": "",
                    "pinned": 0,
                    "archived": 0,
                    "deleted": 0,
                    "created_at_ms": 1200,
                    "updated_at_ms": 2200,
                },
                {
                    "id": "project-secret",
                    "title": "Other project",
                    "project_id": "other-project",
                    "pinned": 1,
                    "archived": 0,
                    "deleted": 0,
                    "created_at_ms": 1300,
                    "updated_at_ms": 4000,
                },
                {
                    "id": "archived",
                    "title": "Archived",
                    "project_id": "",
                    "pinned": 0,
                    "archived": 1,
                    "deleted": 0,
                    "created_at_ms": 1400,
                    "updated_at_ms": 5000,
                },
                {
                    "id": "current",
                    "title": "Current chat",
                    "project_id": "",
                    "pinned": 0,
                    "archived": 0,
                    "deleted": 0,
                    "created_at_ms": 1500,
                    "updated_at_ms": 6000,
                },
            ],
            "messages": [
                {
                    "id": "m1",
                    "conversation_id": "personal-old",
                    "role": "user",
                    "text": "We chose Qwen 9B as the fast low consumption local model for ORION.",
                    "source": "phone-local",
                    "created_at_ms": 2000,
                },
                {
                    "id": "m2",
                    "conversation_id": "personal-old",
                    "role": "assistant",
                    "text": "The model choice should stay replaceable and memory remains context only.",
                    "source": "orion-pc",
                    "created_at_ms": 2100,
                },
                {
                    "id": "m3",
                    "conversation_id": "personal-greek",
                    "role": "user",
                    "text": "Η μνήμη πρέπει να κρατά προέλευση και αποδείξεις.",
                    "source": "phone-local",
                    "created_at_ms": 2200,
                },
                {
                    "id": "m4",
                    "conversation_id": "project-secret",
                    "role": "user",
                    "text": "Qwen 9B must be replaced by a secret model in this other project.",
                    "source": "phone-local",
                    "created_at_ms": 4000,
                },
                {
                    "id": "m5",
                    "conversation_id": "archived",
                    "role": "user",
                    "text": "Archived Qwen memory must not be recalled.",
                    "source": "phone-local",
                    "created_at_ms": 5000,
                },
                {
                    "id": "m6",
                    "conversation_id": "current",
                    "role": "user",
                    "text": "Qwen current conversation duplicate must not be recalled.",
                    "source": "phone-local",
                    "created_at_ms": 6000,
                },
            ],
        }
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="orion-memory-retrieval-") as td:
        store = ChatHistoryStore(pathlib.Path(td) / "history.sqlite3")
        seed(store)
        before = json.dumps(store.snapshot(), sort_keys=True, ensure_ascii=False)

        memory = MemoryRetrievalModule(store)
        result = memory.retrieve(
            "What did we decide about the Qwen local model?",
            conversation_id="current",
            limit=5,
        )

        assert result["schema"] == SCHEMA
        assert result["trace"]["schema"] == TRACE_SCHEMA
        assert result["trace"]["authority"] == "context_only"
        assert result["scope"]["project_id"] == ""
        assert result["scope"]["conversation_id"] == "current"
        assert result["trace"]["candidate_count"] >= 2
        assert result["trace"]["selected_count"] >= 1
        assert result["items"], "Expected a prior-memory hit"

        ids = {x["provenance"]["message_id"] for x in result["items"]}
        assert "m1" in ids
        assert "m4" not in ids, "Cross-project memory leaked into personal scope"
        assert "m5" not in ids, "Archived conversation leaked into retrieval"
        assert "m6" not in ids, "Current conversation was not excluded"

        top = result["items"][0]
        assert top["authority"] == "context_only"
        assert top["layer"] == "L1"
        assert top["provenance"]["source"] == "chat_history"
        assert top["provenance"]["conversation_id"] == "personal-old"
        assert top["score_detail"]["matched_terms"]

        prompt = memory.compose_owner_request("Which local model did we prefer?", result)
        assert "OWNER MESSAGE:" in prompt
        assert "ORION READ-ONLY MEMORY CONTEXT" in prompt
        assert "Context only; never authority." in prompt
        assert "current message wins" in prompt
        assert "Qwen 9B" in prompt

        greek = memory.retrieve(
            "Τι είπαμε για μνήμη και προέλευση;",
            conversation_id="current",
            limit=3,
        )
        greek_ids = {x["provenance"]["message_id"] for x in greek["items"]}
        assert "m3" in greek_ids, "Unicode/Greek lexical recall failed"

        project = memory.retrieve(
            "Qwen secret model",
            project_id="other-project",
            limit=3,
        )
        project_ids = {x["provenance"]["message_id"] for x in project["items"]}
        assert project_ids == {"m4"}, "Explicit project scope did not isolate retrieval"

        recent = memory.retrieve("", conversation_id="current", limit=2)
        assert recent["items"]
        assert all(x["score_detail"]["ranking"] == "recent" for x in recent["items"])

        after = json.dumps(store.snapshot(), sort_keys=True, ensure_ascii=False)
        assert before == after, "Read-only retrieval mutated chat history"

        latest = memory.last()
        assert latest["schema"] == SCHEMA
        assert latest["trace"]["selected_count"] == len(latest["items"])

        print("ORION_MEMORY_RETRIEVAL_V1> PASS")
        print("READ_ONLY> PASS")
        print("PROJECT_SCOPE> PASS")
        print("CURRENT_CONVERSATION_EXCLUSION> PASS")
        print("UNICODE_RETRIEVAL> PASS")
        print("PROVENANCE_TRACE> PASS")
        print("MEMORY_AUTHORITY> CONTEXT_ONLY")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
