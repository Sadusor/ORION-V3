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
from modules.memory_candidate_queue import (
    CanonicalMemoryCandidateQueue,
    MemoryCandidateError,
)


def seed(store: ChatHistoryStore) -> None:
    store.sync(
        {
            "conversations": [
                {
                    "id": "default-chat",
                    "title": "Default",
                    "project_id": "",
                    "pinned": 0,
                    "archived": 0,
                    "deleted": 0,
                    "created_at_ms": 1000,
                    "updated_at_ms": 2000,
                },
                {
                    "id": "project-chat",
                    "title": "Project",
                    "project_id": "project-a",
                    "pinned": 0,
                    "archived": 0,
                    "deleted": 0,
                    "created_at_ms": 1100,
                    "updated_at_ms": 2100,
                },
                {
                    "id": "archived-chat",
                    "title": "Archived",
                    "project_id": "",
                    "pinned": 0,
                    "archived": 1,
                    "deleted": 0,
                    "created_at_ms": 1200,
                    "updated_at_ms": 2200,
                },
            ],
            "messages": [
                {
                    "id": "u1",
                    "conversation_id": "default-chat",
                    "role": "user",
                    "text": "My preferred local model is Qwen 9B.",
                    "source": "phone-pc",
                    "created_at_ms": 2000,
                },
                {
                    "id": "a1",
                    "conversation_id": "project-chat",
                    "role": "assistant",
                    "text": "This prior assistant statement might be useful later.",
                    "source": "orion-pc",
                    "created_at_ms": 2100,
                },
                {
                    "id": "u2",
                    "conversation_id": "archived-chat",
                    "role": "user",
                    "text": "Archived source should not be queueable.",
                    "source": "phone-pc",
                    "created_at_ms": 2200,
                },
            ],
        }
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="orion-candidate-queue-") as td:
        history = ChatHistoryStore(pathlib.Path(td) / "history.sqlite3")
        seed(history)
        before = json.dumps(history.snapshot(), sort_keys=True, ensure_ascii=False)
        queue = CanonicalMemoryCandidateQueue(
            pathlib.Path(td) / "memory_candidates.sqlite3",
            history,
        )

        first = queue.enqueue_chat_message(
            conversation_id="default-chat",
            message_id="u1",
            project_id="",
        )
        assert first["ok"] is True
        assert first["created"] is True
        assert first["canonical_memory_written"] is False
        c = first["candidate"]
        assert c["content"] == "My preferred local model is Qwen 9B."
        assert c["source_message_id"] == "u1"
        assert c["source_conversation_id"] == "default-chat"
        assert c["source_ref"] == "chat_history:default-chat:u1"
        assert c["trust_origin"] == "user"
        assert c["trust_tier"] == "owner_message_unverified"
        assert c["decision"] == "pending"
        assert c["canonical"] is False
        assert c["authority"] == "candidate_only"
        assert len(c["content_sha256"]) == 64

        duplicate = queue.enqueue_chat_message(
            conversation_id="default-chat",
            message_id="u1",
            project_id="",
        )
        assert duplicate["created"] is False
        assert duplicate["candidate"]["candidate_id"] == c["candidate_id"]

        assistant = queue.enqueue_chat_message(
            conversation_id="project-chat",
            message_id="a1",
            project_id="project-a",
        )["candidate"]
        assert assistant["trust_origin"] == "derived"
        assert assistant["trust_tier"] == "assistant_prior_unverified"

        listed = queue.list()
        assert listed["schema"] == "orion.memory-candidate-queue/1"
        assert listed["canonical_memory_written"] is False
        assert listed["count"] == 2
        assert all(x["decision"] == "pending" for x in listed["candidates"])

        try:
            queue.enqueue_chat_message(
                conversation_id="project-chat",
                message_id="a1",
                project_id="wrong-project",
            )
            raise AssertionError("Project mismatch was accepted")
        except MemoryCandidateError as exc:
            assert "scope mismatch" in str(exc)

        try:
            queue.enqueue_chat_message(
                conversation_id="archived-chat",
                message_id="u2",
            )
            raise AssertionError("Archived source was accepted")
        except MemoryCandidateError as exc:
            assert "Archived" in str(exc)

        try:
            queue.enqueue_chat_message(
                conversation_id="default-chat",
                message_id="missing",
            )
            raise AssertionError("Missing source was accepted")
        except MemoryCandidateError as exc:
            assert "not found" in str(exc)

        try:
            queue.enqueue_chat_message(
                conversation_id="default-chat",
                message_id="u1",
                owner_scope="owner:guest",
            )
            raise AssertionError("Unexpected owner scope was accepted")
        except MemoryCandidateError as exc:
            assert "owner_scope" in str(exc)

        after = json.dumps(history.snapshot(), sort_keys=True, ensure_ascii=False)
        assert before == after, "Candidate queue mutated chat history"

        print("ORION_MEMORY_CANDIDATE_QUEUE_V1> PASS")
        print("EXACT_SOURCE_SNAPSHOT> PASS")
        print("IDEMPOTENT_DEDUPE> PASS")
        print("PROJECT_SCOPE> PASS")
        print("ARCHIVED_SOURCE_DENIED> PASS")
        print("OWNER_SCOPE> PASS")
        print("CHAT_HISTORY_IMMUTABLE> PASS")
        print("CANONICAL_MEMORY_WRITE> NONE")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
