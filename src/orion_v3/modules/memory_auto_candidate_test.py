from __future__ import annotations

import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
PARENT = HERE.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from modules.chat_history import ChatHistoryStore
from modules.memory_candidate_queue import CanonicalMemoryCandidateQueue
from modules.memory_auto_candidate import AutomaticMemoryCandidateSelector


def sync_one(store: ChatHistoryStore, mid: str, text: str, ts: int = 2000) -> dict:
    payload = {
        "conversations": [{
            "id": "c1",
            "title": "Auto memory",
            "project_id": "",
            "pinned": 0,
            "archived": 0,
            "deleted": 0,
            "created_at_ms": 1000,
            "updated_at_ms": ts,
        }],
        "messages": [{
            "id": mid,
            "conversation_id": "c1",
            "role": "user",
            "text": text,
            "source": "phone-pc",
            "created_at_ms": ts,
        }],
    }
    store.sync(payload)
    return payload


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="orion-memory-auto-") as td:
        root = pathlib.Path(td)
        history = ChatHistoryStore(root / "history.sqlite3")

        # Existing history must not be backfilled merely because the selector starts.
        sync_one(history, "old1", "My preferred editor is VS Code.", 1500)
        queue = CanonicalMemoryCandidateQueue(root / "candidates.sqlite3", history)
        selector = AutomaticMemoryCandidateSelector(history, queue)
        selector.consider_sync(history.snapshot())
        assert queue.list()["count"] == 0, "Existing history was auto-backfilled"

        # Stable owner preference -> candidate.
        p1 = sync_one(history, "m1", "I prefer Qwen 9B for the fast local manager.", 2000)
        r1 = selector.consider_sync(p1)
        assert r1["new_candidates"] == 1
        listed = queue.list()
        assert listed["count"] == 1
        c = listed["candidates"][0]
        assert c["source_message_id"] == "m1"
        assert c["reason_for_candidate"] == "automatic_stable_owner_statement:preference"
        assert c["canonical"] is False
        assert c["authority"] == "candidate_only"

        # Same payload is idempotent.
        r2 = selector.consider_sync(p1)
        assert r2["new_candidates"] == 0
        assert queue.list()["count"] == 1

        # Questions, transient tests, task requests, and secrets are ignored.
        for i, text in enumerate([
            "What model should we use for ORION?",
            "SYNC TEST 99",
            "I want you to open Chrome and search for a price.",
            "My api key: abcdefghijklmnop",
        ], start=2):
            payload = sync_one(history, f"m{i}", text, 2000 + i)
            result = selector.consider_sync(payload)
            assert result["new_candidates"] == 0, text

        # Stable declarative naming fact -> candidate without explicit 'remember'.
        p6 = sync_one(history, "m6", "The blue box is called NOVA-18.", 2010)
        r6 = selector.consider_sync(p6)
        assert r6["new_candidates"] == 1
        assert queue.list()["count"] == 2

        print("ORION_MEMORY_AUTO_CANDIDATE_V1> PASS")
        print("NO_EXPLICIT_REMEMBER_REQUIRED> PASS")
        print("NO_STARTUP_BACKFILL> PASS")
        print("QUESTIONS_AND_TESTS_FILTERED> PASS")
        print("TASK_REQUESTS_FILTERED> PASS")
        print("SECRETS_FILTERED> PASS")
        print("CANONICAL_MEMORY_WRITE> NONE")
        print("OWNER_REVIEW_REQUIRED> PASS")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
