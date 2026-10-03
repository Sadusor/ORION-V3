from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from orion_v3.state import (
    EventType,
    LocalEventExchange,
    OrionStateStore,
    StateStoreError,
)


def make_exchange(tmp_path: Path):
    path = tmp_path / "orion-core.db"
    store = OrionStateStore(path)
    store.initialize()
    project = store.create_project("ORION", project_id="orion")
    task = store.create_task(
        project.project_id,
        "Build the local exchange",
        task_id="task-1",
    )
    return path, store, LocalEventExchange(store), project, task


def test_external_ingestion_is_idempotent_and_collision_safe(tmp_path: Path):
    _, store, exchange, project, task = make_exchange(tmp_path)

    first = exchange.ingest_external(
        project.project_id,
        task.task_id,
        EventType.PROPOSAL,
        source_system="gemini",
        external_message_id="msg-001",
        actor_kind="cloud_ai",
        actor_id="gemini",
        recipient="reviewer",
        body={"proposal": "Use a local event ledger."},
    )
    assert first.duplicate is False

    duplicate = exchange.ingest_external(
        project.project_id,
        task.task_id,
        EventType.PROPOSAL,
        source_system="gemini",
        external_message_id="msg-001",
        actor_kind="cloud_ai",
        actor_id="gemini",
        recipient="reviewer",
        body={"proposal": "Use a local event ledger."},
    )
    assert duplicate.duplicate is True
    assert duplicate.event.event_id == first.event.event_id
    assert len(store.list_task_events(project.project_id, task.task_id)) == 1

    with pytest.raises(StateStoreError, match="collision"):
        exchange.ingest_external(
            project.project_id,
            task.task_id,
            EventType.PROPOSAL,
            source_system="gemini",
            external_message_id="msg-001",
            actor_kind="cloud_ai",
            actor_id="gemini",
            recipient="reviewer",
            body={"proposal": "Different immutable content."},
        )


def test_inbox_acknowledgement_is_separate_from_immutable_event(tmp_path: Path):
    _, store, exchange, project, task = make_exchange(tmp_path)

    proposal = exchange.ingest_external(
        project.project_id,
        task.task_id,
        EventType.PROPOSAL,
        source_system="gemini",
        external_message_id="msg-001",
        actor_kind="cloud_ai",
        actor_id="gemini",
        recipient="reviewer",
        body={"proposal": "A"},
    )

    inbox = exchange.inbox(
        project.project_id,
        task.task_id,
        "reviewer",
    )
    assert [item.event_id for item in inbox] == [proposal.event.event_id]
    assert inbox[0].acknowledged is False

    exchange.acknowledge(
        project.project_id,
        proposal.event.event_id,
        "reviewer",
    )
    exchange.acknowledge(
        project.project_id,
        proposal.event.event_id,
        "reviewer",
    )
    assert exchange.inbox(
        project.project_id,
        task.task_id,
        "reviewer",
    ) == []

    all_messages = exchange.inbox(
        project.project_id,
        task.task_id,
        "reviewer",
        pending_only=False,
    )
    assert len(all_messages) == 1
    assert all_messages[0].acknowledged is True

    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        store.connect().execute(
            """
            UPDATE exchange_receipts
            SET recipient='tampered'
            WHERE event_id=?
            """,
            (proposal.event.event_id,),
        )
    store.connect().rollback()

    persisted = store.get_event(proposal.event.event_id)
    assert persisted is not None
    assert persisted.payload["body"] == {"proposal": "A"}


def test_full_exchange_chain_is_causal_and_task_scoped(tmp_path: Path):
    _, store, exchange, project, task = make_exchange(tmp_path)

    proposal = exchange.ingest_external(
        project.project_id,
        task.task_id,
        EventType.PROPOSAL,
        source_system="gemini",
        external_message_id="proposal-1",
        actor_kind="cloud_ai",
        actor_id="gemini",
        recipient="reviewer",
        body={"proposal": "Use event ledger."},
    ).event

    review = exchange.ingest_external(
        project.project_id,
        task.task_id,
        EventType.REVIEW,
        source_system="groq",
        external_message_id="review-1",
        actor_kind="cloud_ai",
        actor_id="groq",
        recipient="orion",
        body={"verdict": "accept", "notes": "Keep authority local."},
        parent_event_id=proposal.event_id,
    ).event

    decision = exchange.publish(
        project.project_id,
        task.task_id,
        EventType.DECISION,
        actor_kind="orion",
        actor_id="policy",
        recipient="coding_factory",
        body={"decision": "execute"},
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
        attempt_id="attempt-1",
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
        attempt_id="attempt-1",
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
        attempt_id="attempt-1",
    ).event

    events = store.list_task_events(project.project_id, task.task_id, limit=20)
    assert [event.event_type for event in events] == [
        EventType.PROPOSAL,
        EventType.REVIEW,
        EventType.DECISION,
        EventType.ACTION,
        EventType.EVIDENCE,
        EventType.RESULT,
    ]
    assert [event.parent_event_id for event in events] == [
        None,
        proposal.event_id,
        review.event_id,
        decision.event_id,
        action.event_id,
        evidence.event_id,
    ]
    assert events[-1].event_id == result.event_id


def test_cross_task_parent_is_denied(tmp_path: Path):
    _, store, exchange, project, task = make_exchange(tmp_path)
    other = store.create_task(
        project.project_id,
        "Another task",
        task_id="task-2",
    )
    proposal = exchange.publish(
        project.project_id,
        task.task_id,
        EventType.PROPOSAL,
        actor_kind="owner",
        actor_id="human",
        recipient="reviewer",
        body={"proposal": "A"},
    ).event

    with pytest.raises(StateStoreError, match="another task"):
        exchange.publish(
            project.project_id,
            other.task_id,
            EventType.REVIEW,
            actor_kind="cloud_ai",
            actor_id="reviewer",
            recipient="orion",
            body={"review": "wrong task"},
            parent_event_id=proposal.event_id,
        )


def test_task_packet_is_bounded_project_scoped_and_reopen_safe(tmp_path: Path):
    path, store, exchange, project, task = make_exchange(tmp_path)
    foreign = store.create_project("Foreign", project_id="foreign")
    foreign_task = store.create_task(
        foreign.project_id,
        "Foreign work",
        task_id="foreign-task",
    )

    parent_id = None
    for index in range(5):
        event = exchange.publish(
            project.project_id,
            task.task_id,
            EventType.EVIDENCE,
            actor_kind="probe",
            actor_id="run-016",
            recipient="orion",
            body={"index": index},
            parent_event_id=parent_id,
        ).event
        parent_id = event.event_id

    exchange.publish(
        foreign.project_id,
        foreign_task.task_id,
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
    assert packet["task"]["task_id"] == "task-1"
    assert [item["payload"]["body"]["index"] for item in packet["events"]] == [2, 3, 4]
    assert all(item["actor_id"] != "foreign" for item in packet["events"])
    assert packet["project_context"]["project"]["project_id"] == "orion"

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


def test_exchange_rejects_non_live_memory_event_type(tmp_path: Path):
    _, _, exchange, project, task = make_exchange(tmp_path)
    with pytest.raises(StateStoreError, match="not valid for the live exchange"):
        exchange.publish(
            project.project_id,
            task.task_id,
            EventType.MEMORY_PROMOTED,
            actor_kind="memory_gate",
            actor_id="owner",
            recipient="orion",
            body={"memory": "x"},
        )
