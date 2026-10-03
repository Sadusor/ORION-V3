from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from orion_v3.state import (
    EventType,
    LocalEventExchange,
    OrionStateStore,
    StateStoreError,
)


def main() -> int:
    print("V3_RUN_ID> V3-RUN-016")
    print("LOCAL_EVENT_EXCHANGE_GATE> START")

    with tempfile.TemporaryDirectory(prefix="orion-v3-exchange-") as temp:
        path = Path(temp) / "orion-core.db"
        store = OrionStateStore(path)
        store.initialize()
        project = store.create_project("ORION", project_id="orion")
        task = store.create_task(
            project.project_id,
            "Prove local exchange",
            task_id="task-main",
        )
        other_task = store.create_task(
            project.project_id,
            "Separate task",
            task_id="task-other",
        )
        other_project = store.create_project("Other", project_id="other")
        other_project_task = store.create_task(
            other_project.project_id,
            "Foreign task",
            task_id="foreign-task",
        )
        exchange = LocalEventExchange(store)
        print("EXCHANGE_DB_SETUP> PASS")

        proposal_first = exchange.ingest_external(
            project.project_id,
            task.task_id,
            EventType.PROPOSAL,
            source_system="gemini",
            external_message_id="proposal-001",
            actor_kind="cloud_ai",
            actor_id="gemini",
            recipient="cloud_ai:reviewer",
            body={"proposal": "Use the local Event Ledger as the mailbox."},
        )
        proposal_duplicate = exchange.ingest_external(
            project.project_id,
            task.task_id,
            EventType.PROPOSAL,
            source_system="gemini",
            external_message_id="proposal-001",
            actor_kind="cloud_ai",
            actor_id="gemini",
            recipient="cloud_ai:reviewer",
            body={"proposal": "Use the local Event Ledger as the mailbox."},
        )
        assert proposal_first.duplicate is False
        assert proposal_duplicate.duplicate is True
        assert proposal_first.event.event_id == proposal_duplicate.event.event_id
        assert len(store.list_task_events(project.project_id, task.task_id)) == 1
        print("EXTERNAL_IDEMPOTENCY> PASS")

        try:
            exchange.ingest_external(
                project.project_id,
                task.task_id,
                EventType.PROPOSAL,
                source_system="gemini",
                external_message_id="proposal-001",
                actor_kind="cloud_ai",
                actor_id="gemini",
                recipient="cloud_ai:reviewer",
                body={"proposal": "Different immutable content."},
            )
        except StateStoreError:
            pass
        else:
            raise AssertionError("conflicting external message id was accepted")
        print("EXTERNAL_ID_COLLISION> DENIED")

        inbox = exchange.inbox(
            project.project_id,
            task.task_id,
            "cloud_ai:reviewer",
        )
        assert [message.event_id for message in inbox] == [
            proposal_first.event.event_id
        ]
        exchange.acknowledge(
            project.project_id,
            proposal_first.event.event_id,
            "cloud_ai:reviewer",
        )
        assert exchange.inbox(
            project.project_id,
            task.task_id,
            "cloud_ai:reviewer",
        ) == []
        all_reviewer = exchange.inbox(
            project.project_id,
            task.task_id,
            "cloud_ai:reviewer",
            pending_only=False,
        )
        assert len(all_reviewer) == 1 and all_reviewer[0].acknowledged is True
        proposal_after_ack = store.get_event(proposal_first.event.event_id)
        assert proposal_after_ack is not None
        assert proposal_after_ack.payload["body"] == {
            "proposal": "Use the local Event Ledger as the mailbox."
        }
        print("RECIPIENT_INBOX_ACK_SEPARATION> PASS")

        try:
            store.connect().execute(
                """
                UPDATE exchange_receipts
                SET recipient='tampered'
                WHERE event_id=?
                """,
                (proposal_first.event.event_id,),
            )
        except sqlite3.IntegrityError:
            store.connect().rollback()
        else:
            raise AssertionError("exchange receipt mutation unexpectedly succeeded")
        print("RECEIPT_APPEND_ONLY_TRIGGER> PASS")

        review = exchange.ingest_external(
            project.project_id,
            task.task_id,
            EventType.REVIEW,
            source_system="groq",
            external_message_id="review-001",
            actor_kind="cloud_ai",
            actor_id="groq",
            recipient="orion",
            body={"verdict": "accept", "note": "Keep authority local."},
            parent_event_id=proposal_first.event.event_id,
        ).event

        decision = exchange.publish(
            project.project_id,
            task.task_id,
            EventType.DECISION,
            actor_kind="orion",
            actor_id="policy",
            recipient="coding_factory",
            body={"decision": "dispatch bounded action"},
            parent_event_id=review.event_id,
        ).event

        action = exchange.publish(
            project.project_id,
            task.task_id,
            EventType.ACTION,
            actor_kind="orion",
            actor_id="coding_factory",
            recipient="hand:coding",
            body={"capability": "project.run_tests"},
            parent_event_id=decision.event_id,
            attempt_id="attempt-001",
        ).event

        evidence = exchange.publish(
            project.project_id,
            task.task_id,
            EventType.EVIDENCE,
            actor_kind="hand",
            actor_id="coding",
            recipient="orion",
            body={"exit_code": 0, "tests": "64 passed"},
            parent_event_id=action.event_id,
            attempt_id="attempt-001",
        ).event

        result = exchange.publish(
            project.project_id,
            task.task_id,
            EventType.RESULT,
            actor_kind="orion",
            actor_id="verifier",
            recipient="cloud_ai:architect",
            body={"status": "PASS"},
            parent_event_id=evidence.event_id,
            attempt_id="attempt-001",
        ).event

        chain = store.list_task_events(project.project_id, task.task_id, limit=20)
        assert [event.event_type for event in chain] == [
            EventType.PROPOSAL,
            EventType.REVIEW,
            EventType.DECISION,
            EventType.ACTION,
            EventType.EVIDENCE,
            EventType.RESULT,
        ]
        assert [event.parent_event_id for event in chain] == [
            None,
            proposal_first.event.event_id,
            review.event_id,
            decision.event_id,
            action.event_id,
            evidence.event_id,
        ]
        assert chain[-1].event_id == result.event_id
        print("FULL_CAUSAL_EXCHANGE_CHAIN> PASS")

        try:
            exchange.publish(
                project.project_id,
                other_task.task_id,
                EventType.REVIEW,
                actor_kind="cloud_ai",
                actor_id="reviewer",
                recipient="orion",
                body={"review": "wrong task"},
                parent_event_id=proposal_first.event.event_id,
            )
        except StateStoreError:
            pass
        else:
            raise AssertionError("cross-task parent unexpectedly accepted")
        print("CROSS_TASK_PARENT> DENIED")

        exchange.publish(
            other_project.project_id,
            other_project_task.task_id,
            EventType.EVIDENCE,
            actor_kind="probe",
            actor_id="foreign",
            recipient="orion",
            body={"foreign": True},
        )

        packet = exchange.task_packet(
            project.project_id,
            task.task_id,
            limit=3,
        )
        assert packet["task"]["task_id"] == "task-main"
        assert [event["event_type"] for event in packet["events"]] == [
            "ACTION",
            "EVIDENCE",
            "RESULT",
        ]
        assert packet["events"][-1]["event_id"] == result.event_id
        assert all(event["actor_id"] != "foreign" for event in packet["events"])
        assert packet["project_context"]["project"]["project_id"] == "orion"
        print("BOUNDED_TASK_PACKET_SCOPE> PASS")

        store.close()
        reopened = OrionStateStore(path)
        reopened.initialize()
        reopened_exchange = LocalEventExchange(reopened)
        packet_after = reopened_exchange.task_packet(
            project.project_id,
            task.task_id,
            limit=3,
        )
        assert packet_after["events"] == packet["events"]
        assert reopened_exchange.inbox(
            project.project_id,
            task.task_id,
            "cloud_ai:reviewer",
        ) == []
        all_after = reopened_exchange.inbox(
            project.project_id,
            task.task_id,
            "cloud_ai:reviewer",
            pending_only=False,
        )
        assert len(all_after) == 1 and all_after[0].acknowledged is True
        print("EXCHANGE_REOPEN_PERSISTENCE> PASS")

        print("GITHUB_NETWORK_MODEL_DEPENDENCY> NONE")
        print("LOCAL_EVENT_EXCHANGE_GATE> PASS")
        print("STATUS> PASS")
        reopened.close()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
