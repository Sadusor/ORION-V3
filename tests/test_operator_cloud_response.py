from pathlib import Path

import pytest

from orion_v3.operator import OperatorControlDenied, OperatorControlPlane
from orion_v3.state import EventType, LocalEventExchange, OrionStateStore, StateStoreError


def make_control(tmp_path: Path):
    store = OrionStateStore(tmp_path / "orion.db")
    store.initialize()
    project = store.create_project("Cloud Response", project_id="project-cloud-response")
    task = store.create_task(
        project.project_id,
        "Route coding specialist",
        task_id="task-cloud-response",
    )
    control = OperatorControlPlane(store)
    control.initialize()
    queued = control.queue_cloud_specialist(
        task.task_id,
        specialty="coding",
        task="Refactor the parser and review the patch.",
        requested_by="qwen35-9b-orion",
    )
    return store, control, task, queued.request


def test_cloud_response_is_advisory_review_bound_to_exact_request(tmp_path: Path):
    store, control, task, request = make_control(tmp_path)

    result = control.ingest_cloud_specialist_response(
        request.request_id,
        source_system="fixture-cloud",
        external_message_id="message-1",
        provider_id="groq",
        model_id="openai/gpt-oss-120b",
        response_text="Proposed coding plan only. Do not execute.",
    )

    event = store.get_event(result.event_id)
    assert event is not None
    assert event.event_type == EventType.REVIEW
    assert event.parent_event_id == request.event_id
    assert event.actor_kind == "cloud_specialist"
    assert event.actor_id == "groq:openai/gpt-oss-120b"
    assert event.payload["recipient"] == "orion:governor"
    body = event.payload["body"]
    assert body["kind"] == "cloud_specialist_response"
    assert body["request_id"] == request.request_id
    assert body["request_sha256"] == request.request_sha256
    assert body["specialty"] == "coding"
    assert body["provider_id"] == "groq"
    assert body["model_id"] == "openai/gpt-oss-120b"
    assert body["response_text"] == "Proposed coding plan only. Do not execute."
    assert body["authority"] == "advisory_only"
    assert body["response_sha256"] == result.response_sha256

    events = store.list_task_events(task.project_id, task.task_id)
    assert [event.event_type for event in events] == [
        EventType.PROPOSAL,
        EventType.REVIEW,
    ]
    assert all(event.event_type not in {EventType.DECISION, EventType.ACTION} for event in events)


def test_cloud_response_duplicate_is_idempotent_and_collision_fails_closed(tmp_path: Path):
    _, control, _, request = make_control(tmp_path)

    first = control.ingest_cloud_specialist_response(
        request.request_id,
        source_system="fixture-cloud",
        external_message_id="same-message",
        provider_id="groq",
        model_id="openai/gpt-oss-120b",
        response_text="Same immutable response.",
    )
    second = control.ingest_cloud_specialist_response(
        request.request_id,
        source_system="fixture-cloud",
        external_message_id="same-message",
        provider_id="groq",
        model_id="openai/gpt-oss-120b",
        response_text="Same immutable response.",
    )

    assert first.duplicate is False
    assert second.duplicate is True
    assert second.event_id == first.event_id
    assert second.response_sha256 == first.response_sha256

    with pytest.raises(StateStoreError):
        control.ingest_cloud_specialist_response(
            request.request_id,
            source_system="fixture-cloud",
            external_message_id="same-message",
            provider_id="groq",
            model_id="openai/gpt-oss-120b",
            response_text="Different content under reused external id.",
        )


def test_cloud_response_enters_governor_inbox_without_authority(tmp_path: Path):
    store, control, task, request = make_control(tmp_path)
    exchange = LocalEventExchange(store)

    result = control.ingest_cloud_specialist_response(
        request.request_id,
        source_system="fixture-cloud",
        external_message_id="message-2",
        provider_id="gemini",
        model_id="gemini-test-model",
        response_text="Advisory review response.",
    )

    inbox = exchange.inbox(
        task.project_id,
        task.task_id,
        "orion:governor",
    )
    assert len(inbox) == 1
    assert inbox[0].event_id == result.event_id
    assert inbox[0].event_type == EventType.REVIEW
    assert inbox[0].body["authority"] == "advisory_only"


def test_cloud_response_unknown_request_is_denied(tmp_path: Path):
    store = OrionStateStore(tmp_path / "orion.db")
    store.initialize()
    project = store.create_project("Unknown", project_id="project-unknown")
    store.create_task(project.project_id, "Unknown request", task_id="task-unknown")
    control = OperatorControlPlane(store)
    control.initialize()

    with pytest.raises(OperatorControlDenied) as exc:
        control.ingest_cloud_specialist_response(
            "missing-request",
            source_system="fixture-cloud",
            external_message_id="message-x",
            provider_id="groq",
            model_id="model",
            response_text="response",
        )
    assert exc.value.code == "unknown_cloud_request"


def test_cloud_response_survives_restart(tmp_path: Path):
    db = tmp_path / "orion.db"
    store = OrionStateStore(db)
    store.initialize()
    project = store.create_project("Persistent Cloud", project_id="project-persistent-cloud")
    task = store.create_task(
        project.project_id,
        "Persistent cloud task",
        task_id="task-persistent-cloud",
    )
    control = OperatorControlPlane(store)
    control.initialize()
    request = control.queue_cloud_specialist(
        task.task_id,
        specialty="review",
        task="Review one bounded result.",
        requested_by="qwen35-9b-orion",
    ).request
    response = control.ingest_cloud_specialist_response(
        request.request_id,
        source_system="fixture-cloud",
        external_message_id="persistent-message",
        provider_id="groq",
        model_id="review-model",
        response_text="Persistent advisory review.",
    )
    store.close()

    reopened = OrionStateStore(db)
    reopened.initialize()
    event = reopened.get_event(response.event_id)
    assert event is not None
    assert event.event_type == EventType.REVIEW
    assert event.parent_event_id == request.event_id
    assert event.payload["body"]["authority"] == "advisory_only"
    reopened.close()
