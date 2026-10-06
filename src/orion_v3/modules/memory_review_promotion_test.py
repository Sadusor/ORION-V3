from __future__ import annotations

import json
import pathlib
import sqlite3
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
PARENT = HERE.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from modules.chat_history import ChatHistoryStore
from modules.memory_candidate_queue import CanonicalMemoryCandidateQueue
from modules.memory_review_promotion import (
    CanonicalMemoryReviewPromotion,
    MemoryReviewError,
)


def seed(history: ChatHistoryStore) -> None:
    history.sync(
        {
            "conversations": [
                {
                    "id": "facts",
                    "title": "Facts",
                    "project_id": "",
                    "pinned": 0,
                    "archived": 0,
                    "deleted": 0,
                    "created_at_ms": 1000,
                    "updated_at_ms": 1500,
                },
                {
                    "id": "project-a",
                    "title": "Project A",
                    "project_id": "A",
                    "pinned": 0,
                    "archived": 0,
                    "deleted": 0,
                    "created_at_ms": 1100,
                    "updated_at_ms": 1600,
                },
            ],
            "messages": [
                {
                    "id": "fact-green",
                    "conversation_id": "facts",
                    "role": "user",
                    "text": "The owner-confirmed STARLING value is GREEN 842.",
                    "source": "phone-pc",
                    "created_at_ms": 1200,
                },
                {
                    "id": "fact-reject",
                    "conversation_id": "facts",
                    "role": "assistant",
                    "text": "An assistant prior says STARLING is BLUE 901.",
                    "source": "orion-pc",
                    "created_at_ms": 1300,
                },
                {
                    "id": "fact-defer",
                    "conversation_id": "project-a",
                    "role": "user",
                    "text": "Project A deployment preference is canary first.",
                    "source": "phone-pc",
                    "created_at_ms": 1400,
                },
                {
                    "id": "fact-secret",
                    "conversation_id": "facts",
                    "role": "user",
                    "text": "api_key = SUPER-SECRET-123456",
                    "source": "phone-pc",
                    "created_at_ms": 1500,
                },
            ],
        }
    )


def enqueue(queue: CanonicalMemoryCandidateQueue, cid: str, mid: str, project: str):
    return queue.enqueue_chat_message(
        conversation_id=cid,
        message_id=mid,
        project_id=project,
    )["candidate"]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="orion-memory-review-") as td:
        root = pathlib.Path(td)
        history = ChatHistoryStore(root / "history.sqlite3")
        seed(history)
        queue = CanonicalMemoryCandidateQueue(root / "candidates.sqlite3", history)
        review = CanonicalMemoryReviewPromotion(root / "canonical.sqlite3", queue)

        green = enqueue(queue, "facts", "fact-green", "")
        wrong = enqueue(queue, "facts", "fact-reject", "")
        defer_c = enqueue(queue, "project-a", "fact-defer", "A")
        secret = enqueue(queue, "facts", "fact-secret", "")

        before_candidates = json.dumps(queue.list(), sort_keys=True, ensure_ascii=False)

        promoted = review.decide(
            candidate_id=green["candidate_id"],
            decision="promote",
            expected_content_sha256=green["content_sha256"],
        )
        assert promoted["ok"] is True
        assert promoted["created"] is True
        assert promoted["canonical_memory_written"] is True
        mem = promoted["memory"]
        assert mem["canonical"] is True
        assert mem["authority"] == "context_only"
        assert mem["content"] == green["content"]
        assert mem["content_sha256"] == green["content_sha256"]
        assert mem["candidate_id"] == green["candidate_id"]
        assert mem["source_ref"] == green["source_ref"]

        # Exact repeated promotion is idempotent, not a second write.
        again = review.decide(
            candidate_id=green["candidate_id"],
            decision="promote",
            expected_content_sha256=green["content_sha256"],
        )
        assert again["created"] is False
        assert again["memory"]["memory_id"] == mem["memory_id"]

        # Terminal decisions cannot be reversed in V1.
        try:
            review.decide(
                candidate_id=green["candidate_id"],
                decision="reject",
                expected_content_sha256=green["content_sha256"],
            )
            raise AssertionError("Promoted candidate was allowed to reverse terminal decision")
        except MemoryReviewError as exc:
            assert "terminal" in str(exc)

        rejected = review.decide(
            candidate_id=wrong["candidate_id"],
            decision="reject",
            expected_content_sha256=wrong["content_sha256"],
        )
        assert rejected["canonical_memory_written"] is False

        deferred = review.decide(
            candidate_id=defer_c["candidate_id"],
            decision="defer",
            expected_content_sha256=defer_c["content_sha256"],
        )
        assert deferred["decision"]["decision"] == "defer"
        assert deferred["canonical_memory_written"] is False

        # Deferred is non-terminal and can later be explicitly promoted.
        deferred_promoted = review.decide(
            candidate_id=defer_c["candidate_id"],
            decision="promote",
            expected_content_sha256=defer_c["content_sha256"],
        )
        assert deferred_promoted["created"] is True
        assert deferred_promoted["canonical_memory_written"] is True
        assert deferred_promoted["memory"]["project_id"] == "A"

        # Stale/forged review state cannot decide another content hash.
        try:
            review.decide(
                candidate_id=secret["candidate_id"],
                decision="reject",
                expected_content_sha256="0" * 64,
            )
            raise AssertionError("Content hash mismatch was accepted")
        except MemoryReviewError as exc:
            assert "hash mismatch" in str(exc)

        # V1 normal memory promotion rejects obvious secret material.
        try:
            review.decide(
                candidate_id=secret["candidate_id"],
                decision="promote",
                expected_content_sha256=secret["content_sha256"],
            )
            raise AssertionError("Secret-like candidate was promoted")
        except MemoryReviewError as exc:
            assert "secret material" in str(exc)

        # It may still be explicitly rejected.
        secret_reject = review.decide(
            candidate_id=secret["candidate_id"],
            decision="reject",
            expected_content_sha256=secret["content_sha256"],
        )
        assert secret_reject["canonical_memory_written"] is False

        view = review.candidates_view()
        by_id = {x["candidate_id"]: x for x in view["candidates"]}
        assert by_id[green["candidate_id"]]["decision"] == "promote"
        assert by_id[green["candidate_id"]]["durable_memory_id"] == mem["memory_id"]
        assert by_id[wrong["candidate_id"]]["decision"] == "reject"
        assert by_id[defer_c["candidate_id"]]["decision"] == "promote"
        assert by_id[secret["candidate_id"]]["decision"] == "reject"
        assert view["promoted_count"] == 2
        assert view["rejected_count"] == 2
        assert view["pending_count"] == 0

        canonical = review.list_canonical()
        assert canonical["authority"] == "context_only"
        assert canonical["count"] == 2
        assert {x["content_sha256"] for x in canonical["memories"]} == {
            green["content_sha256"],
            defer_c["content_sha256"],
        }

        log = review.decisions()
        assert log["append_only"] is True
        # promote green, reject wrong, defer project, promote project, reject secret
        assert log["count"] == 5
        audit = review.audit_chain()
        assert audit["ok"] is True
        assert audit["events"] == 5
        assert len(audit["head_hash"]) == 64

        # SQLite triggers enforce append-only/immutable semantics.
        con = sqlite3.connect(root / "canonical.sqlite3")
        try:
            try:
                con.execute("UPDATE decision_events SET reason='tampered' WHERE seq=1")
                con.commit()
                raise AssertionError("Decision update unexpectedly succeeded")
            except sqlite3.DatabaseError as exc:
                con.rollback()
                assert "append-only" in str(exc)

            try:
                con.execute("DELETE FROM decision_events WHERE seq=1")
                con.commit()
                raise AssertionError("Decision delete unexpectedly succeeded")
            except sqlite3.DatabaseError as exc:
                con.rollback()
                assert "append-only" in str(exc)

            try:
                con.execute("UPDATE canonical_memories SET content='tampered'")
                con.commit()
                raise AssertionError("Canonical memory update unexpectedly succeeded")
            except sqlite3.DatabaseError as exc:
                con.rollback()
                assert "immutable" in str(exc)
        finally:
            con.close()

        # New review module never mutates the frozen candidate queue.
        after_candidates = json.dumps(queue.list(), sort_keys=True, ensure_ascii=False)
        assert before_candidates == after_candidates

        print("ORION_CANONICAL_MEMORY_REVIEW_V1> PASS")
        print("OWNER_PROMOTE> PASS")
        print("OWNER_REJECT> PASS")
        print("OWNER_DEFER_THEN_PROMOTE> PASS")
        print("TERMINAL_DECISION_IMMUTABLE> PASS")
        print("CONTENT_HASH_BINDING> PASS")
        print("SECRET_PROMOTION_DENIED> PASS")
        print("DECISION_LOG_APPEND_ONLY> PASS")
        print("CANONICAL_MEMORY_IMMUTABLE> PASS")
        print("EVENT_HASH_CHAIN> PASS")
        print("FROZEN_CANDIDATE_QUEUE_UNCHANGED> PASS")
        print("CANONICAL_MEMORY_AUTHORITY> CONTEXT_ONLY")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
