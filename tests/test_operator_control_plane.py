from pathlib import Path

import pytest

from orion_v3.operator import ApprovalStatus, OperatorControlDenied, OperatorControlPlane
from orion_v3.state import EventType, LocalEventExchange, OrionStateStore


def make_control(tmp_path: Path):
    db = tmp_path / "orion.db"
    store = OrionStateStore(db)
    store.initialize()
    project = store.create_project("Operator Test", project_id="project-1")
    task = store.create_task(project.project_id, "Do one bounded thing", task_id="task-1")
    other = store.create_task(project.project_id, "Other task", task_id="task-2")
    control = OperatorControlPlane(store)
    control.initialize()
    return store, control, task, other


def test_append_event_can_participate_in_caller_transaction(tmp_path: Path):
    store, _, task, _ = make_control(tmp_path)
    conn = store.connect()

    conn.execute("BEGIN IMMEDIATE")
    event = store.append_event(
        task.project_id,
        EventType.PROPOSAL,
        {"kind": "transaction_probe"},
        actor_kind="test",
        actor_id="unit",
        task_id=task.task_id,
        commit=False,
    )
    conn.rollback()

    assert store.get_event(event.event_id) is None


def test_approval_freezes_exact_action_and_deduplicates(tmp_path: Path):
    store, control, task, _ = make_control(tmp_path)

    first = control.request_approval(
        task.task_id,
        capability_id="project.publish_exact_artifact",
        params={
            "artifact_path": "docs/proof.txt",
            "artifact_content": "exact bytes\n",
        },
        requested_by="qwen35-9b-orion",
    )
    second = control.request_approval(
        task.task_id,
        capability_id="project.publish_exact_artifact",
        params={
            "artifact_content": "exact bytes\n",
            "artifact_path": "docs/proof.txt",
        },
        requested_by="qwen35-9b-orion",
    )

    assert first.duplicate is False
    assert second.duplicate is True
    assert second.approval.approval_id == first.approval.approval_id
    assert first.approval.status == ApprovalStatus.PENDING
    assert first.approval.action.params == {
        "artifact_path": "docs/proof.txt",
        "artifact_content": "exact bytes\n",
    }

    events = store.list_task_events(task.project_id, task.task_id)
    approval_requests = [
        event
        for event in events
        if event.event_type == EventType.PROPOSAL
        and event.payload.get("kind") == "approval_request"
    ]
    assert len(approval_requests) == 1
    assert (
        approval_requests[0].payload["action_sha256"]
        == first.approval.action.action_sha256
    )


def test_non_approval_capability_is_rejected_from_approval_lane(tmp_path: Path):
    _, control, task, _ = make_control(tmp_path)

    with pytest.raises(OperatorControlDenied) as exc:
        control.request_approval(
            task.task_id,
            capability_id="fs.search_exact",
            params={
                "exact_names": ["README.md"],
                "locations": ["active_project"],
            },
            requested_by="qwen35-9b-orion",
        )

    assert exc.value.code == "approval_not_required"


def test_pending_cannot_execute_and_approved_action_is_single_use(tmp_path: Path):
    store, control, task, other = make_control(tmp_path)
    requested = control.request_approval(
        task.task_id,
        capability_id="project.publish_exact_artifact",
        params={
            "artifact_path": "docs/proof.txt",
            "artifact_content": "approved content",
        },
        requested_by="operator",
    )

    with pytest.raises(OperatorControlDenied) as exc:
        control.consume_approved_action(
            requested.approval.approval_id,
            task_id=task.task_id,
            consumed_by="orion",
        )
    assert exc.value.code == "approval_pending"

    approved = control.approve(
        requested.approval.approval_id,
        approved_by="owner",
    )
    duplicate = control.approve(
        requested.approval.approval_id,
        approved_by="owner",
    )
    assert approved.duplicate is False
    assert duplicate.duplicate is True
    assert approved.approval.status == ApprovalStatus.APPROVED

    with pytest.raises(OperatorControlDenied) as exc:
        control.consume_approved_action(
            requested.approval.approval_id,
            task_id=other.task_id,
            consumed_by="orion",
        )
    assert exc.value.code == "wrong_task"

    consumed = control.consume_approved_action(
        requested.approval.approval_id,
        task_id=task.task_id,
        consumed_by="orion",
    )
    assert consumed.approval.status == ApprovalStatus.CONSUMED
    assert consumed.action.capability_id == "project.publish_exact_artifact"
    assert consumed.action.params["artifact_content"] == "approved content"

    with pytest.raises(OperatorControlDenied) as exc:
        control.consume_approved_action(
            requested.approval.approval_id,
            task_id=task.task_id,
            consumed_by="orion",
        )
    assert exc.value.code == "stale_approval"

    events = store.list_task_events(task.project_id, task.task_id)
    kinds = [event.payload.get("kind") for event in events]
    assert kinds == [
        "approval_request",
        "approval_decision",
        "approved_action_consumed",
    ]
    assert events[1].parent_event_id == events[0].event_id
    assert events[2].parent_event_id == events[1].event_id


def test_rejected_approval_never_becomes_executable(tmp_path: Path):
    _, control, task, _ = make_control(tmp_path)
    requested = control.request_approval(
        task.task_id,
        capability_id="project.publish_exact_artifact",
        params={
            "artifact_path": "docs/rejected.txt",
            "artifact_content": "no",
        },
        requested_by="operator",
    )
    rejected = control.reject(
        requested.approval.approval_id,
        rejected_by="owner",
        reason="not wanted",
    )
    duplicate = control.reject(
        requested.approval.approval_id,
        rejected_by="owner",
        reason="not wanted",
    )

    assert rejected.approval.status == ApprovalStatus.REJECTED
    assert duplicate.duplicate is True

    with pytest.raises(OperatorControlDenied) as exc:
        control.consume_approved_action(
            requested.approval.approval_id,
            task_id=task.task_id,
            consumed_by="orion",
        )
    assert exc.value.code == "approval_rejected"


def test_cloud_queue_is_idempotent_and_enters_local_exchange(tmp_path: Path):
    store, control, task, _ = make_control(tmp_path)
    exchange = LocalEventExchange(store)

    first = control.queue_cloud_specialist(
        task.task_id,
        specialty="architecture",
        task="Compare durable memory designs.",
        requested_by="qwen35-9b-orion",
    )
    second = control.queue_cloud_specialist(
        task.task_id,
        specialty="architecture",
        task="Compare durable memory designs.",
        requested_by="qwen35-9b-orion",
    )

    assert first.duplicate is False
    assert second.duplicate is True
    assert second.request.request_id == first.request.request_id
    assert second.request.event_id == first.request.event_id

    inbox = exchange.inbox(
        task.project_id,
        task.task_id,
        "cloud:architecture",
    )
    assert len(inbox) == 1
    assert inbox[0].event_id == first.request.event_id
    assert inbox[0].body["kind"] == "cloud_specialist_request"
    assert inbox[0].body["specialty"] == "architecture"
    assert inbox[0].body["task"] == "Compare durable memory designs."
    assert inbox[0].body["request_sha256"] == first.request.request_sha256


def test_cloud_queue_rejects_unknown_specialty(tmp_path: Path):
    _, control, task, _ = make_control(tmp_path)

    with pytest.raises(OperatorControlDenied) as exc:
        control.queue_cloud_specialist(
            task.task_id,
            specialty="random-agent",
            task="Do anything.",
            requested_by="operator",
        )

    assert exc.value.code == "invalid_cloud_specialty"


def test_control_state_survives_restart(tmp_path: Path):
    db = tmp_path / "persistent.db"
    store = OrionStateStore(db)
    store.initialize()
    project = store.create_project("Persistent", project_id="p")
    task = store.create_task(project.project_id, "Persist", task_id="t")
    control = OperatorControlPlane(store)
    control.initialize()

    requested = control.request_approval(
        task.task_id,
        capability_id="project.publish_exact_artifact",
        params={
            "artifact_path": "docs/persist.txt",
            "artifact_content": "persisted",
        },
        requested_by="operator",
    )
    control.approve(requested.approval.approval_id, approved_by="owner")
    consumed = control.consume_approved_action(
        requested.approval.approval_id,
        task_id=task.task_id,
        consumed_by="orion",
    )
    cloud = control.queue_cloud_specialist(
        task.task_id,
        specialty="review",
        task="Review the frozen result.",
        requested_by="operator",
    )
    store.close()

    reopened = OrionStateStore(db)
    reopened.initialize()
    control2 = OperatorControlPlane(reopened)
    control2.initialize()

    approval2 = control2.get_approval(consumed.approval.approval_id)
    cloud2 = control2.get_cloud_request(cloud.request.request_id)
    assert approval2.status == ApprovalStatus.CONSUMED
    assert approval2.action.action_sha256 == consumed.action.action_sha256
    assert cloud2.request_sha256 == cloud.request.request_sha256
    reopened.close()
