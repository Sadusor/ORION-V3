from pathlib import Path

import pytest

from orion_v3.evidence import EvidenceEnvelope, Outcome
from orion_v3.operator import (
    ContinuationState,
    OperatorControlDenied,
    OperatorControlPlane,
    decide_exact_search_continuation,
    decide_exact_search_task_progress,
    execute_read_only_proposal,
    owner_input_packet,
)
from orion_v3.state import EventType, OrionStateStore


def make_progress(tmp_path: Path, *, include_gateway: bool, truncated: bool = False):
    suffix = "complete" if include_gateway else ("truncated" if truncated else "missing")
    store = OrionStateStore(tmp_path / f"orion-{suffix}.db")
    store.initialize()
    project = store.create_project("Continuation", project_id=f"p-cont-{suffix}")
    task = store.create_task(
        project.project_id,
        "Find pyproject.toml and gateway.py",
        task_id=f"t-cont-{suffix}",
    )
    control = OperatorControlPlane(store)
    control.initialize()
    proposal = control.propose_capability_action(
        task.task_id,
        capability_id="fs.search_exact",
        params={
            "exact_names": ["pyproject.toml", "gateway.py"],
            "locations": ["active_project"],
        },
        proposed_by="qwen35-9b-orion",
    )

    matches = [
        {
            "location": "active_project",
            "relative_path": "pyproject.toml",
            "name": "pyproject.toml",
            "kind": "file",
            "size_bytes": 10,
            "modified_ns": 1,
        }
    ]
    if include_gateway:
        matches.append(
            {
                "location": "active_project",
                "relative_path": "src/orion_v3/authority/gateway.py",
                "name": "gateway.py",
                "kind": "file",
                "size_bytes": 20,
                "modified_ns": 2,
            }
        )

    def runner(task_id, params, trusted_roots):
        return (
            EvidenceEnvelope(
                task_id=task_id,
                lease_id="lease-cont",
                operation_id="filesystem.search",
                implementation_id="openjarvis.tool.orion_filesystem_search.v1",
                outcome=Outcome.CONFIRMED,
                result={
                    "operation_id": "filesystem.search",
                    "implementation_id": "openjarvis.tool.orion_filesystem_search.v1",
                    "searched_locations": ["active_project"],
                    "matches": matches,
                    "match_count": len(matches),
                    "truncated": truncated,
                },
                verifier="orion.openjarvis.filesystem_search.v1",
            ),
            "lease-cont",
        )

    execution = execute_read_only_proposal(
        store,
        task_id=task.task_id,
        proposal_event_id=proposal.event_id,
        trusted_roots={"active_project": tmp_path},
        search_runner=runner,
    )
    progress = decide_exact_search_task_progress(
        store,
        task_id=task.task_id,
        result_event_id=execution.result_event_id,
        required_exact_names=["pyproject.toml", "gateway.py"],
        required_locations=["active_project"],
    )
    return store, task, execution, progress


def test_completed_task_has_no_continuation_action(tmp_path: Path):
    store, task, _, progress = make_progress(tmp_path, include_gateway=True)

    continuation = decide_exact_search_continuation(
        store,
        task_id=task.task_id,
        progress_decision_event_id=progress.decision_event_id,
    )

    assert continuation.state == ContinuationState.COMPLETE_NO_ACTION
    assert continuation.continuation_event_id is None
    assert continuation.missing_names == ()
    task_after = store.get_task(task.task_id)
    assert task_after is not None
    assert task_after.status == "completed"

    events = store.list_task_events(task.project_id, task.task_id)
    assert [event.event_type for event in events] == [
        EventType.PROPOSAL,
        EventType.ACTION,
        EventType.EVIDENCE,
        EventType.RESULT,
        EventType.DECISION,
    ]


def test_exhausted_missing_search_moves_task_to_waiting_owner(tmp_path: Path):
    store, task, _, progress = make_progress(tmp_path, include_gateway=False)

    continuation = decide_exact_search_continuation(
        store,
        task_id=task.task_id,
        progress_decision_event_id=progress.decision_event_id,
    )

    assert continuation.state == ContinuationState.OWNER_INPUT_REQUIRED
    assert continuation.missing_names == ("gateway.py",)
    assert continuation.searched_locations == ("active_project",)
    assert continuation.duplicate is False
    assert continuation.continuation_event_id is not None

    task_after = store.get_task(task.task_id)
    assert task_after is not None
    assert task_after.status == "waiting_owner"

    events = store.list_task_events(task.project_id, task.task_id)
    assert [event.event_type for event in events] == [
        EventType.PROPOSAL,
        EventType.ACTION,
        EventType.EVIDENCE,
        EventType.RESULT,
        EventType.DECISION,
        EventType.DECISION,
    ]
    assert events[-1].parent_event_id == progress.decision_event_id
    assert events[-1].payload["state"] == "OWNER_INPUT_REQUIRED"
    assert events[-1].payload["automatic_retry_allowed"] is False
    assert events[-1].payload["authority"] == "orion_deterministic_policy"


def test_owner_input_continuation_is_idempotent(tmp_path: Path):
    store, task, _, progress = make_progress(tmp_path, include_gateway=False)

    first = decide_exact_search_continuation(
        store,
        task_id=task.task_id,
        progress_decision_event_id=progress.decision_event_id,
    )
    second = decide_exact_search_continuation(
        store,
        task_id=task.task_id,
        progress_decision_event_id=progress.decision_event_id,
    )

    assert first.duplicate is False
    assert second.duplicate is True
    assert second.continuation_event_id == first.continuation_event_id

    events = store.list_task_events(task.project_id, task.task_id)
    continuation_events = [
        event for event in events
        if event.event_type == EventType.DECISION
        and event.payload.get("kind") == "task_continuation"
    ]
    assert len(continuation_events) == 1


def test_owner_input_packet_is_safe_and_exact(tmp_path: Path):
    store, task, _, progress = make_progress(tmp_path, include_gateway=False)
    continuation = decide_exact_search_continuation(
        store,
        task_id=task.task_id,
        progress_decision_event_id=progress.decision_event_id,
    )

    packet = owner_input_packet(
        store,
        task_id=task.task_id,
        continuation_event_id=continuation.continuation_event_id,
    )

    assert packet == {
        "schema": "orion.v3.owner-input-required.v0",
        "task_id": task.task_id,
        "continuation_event_id": continuation.continuation_event_id,
        "state": "OWNER_INPUT_REQUIRED",
        "missing_names": ["gateway.py"],
        "searched_locations": ["active_project"],
        "owner_choices": [
            "provide_new_search_scope",
            "provide_expected_location",
            "stop_task",
        ],
        "automatic_retry_allowed": False,
        "authority": "orion_deterministic_policy",
    }


def test_truncated_search_does_not_guess_a_continuation_strategy(tmp_path: Path):
    store, task, _, progress = make_progress(
        tmp_path,
        include_gateway=False,
        truncated=True,
    )

    with pytest.raises(OperatorControlDenied) as exc:
        decide_exact_search_continuation(
            store,
            task_id=task.task_id,
            progress_decision_event_id=progress.decision_event_id,
        )

    assert exc.value.code == "continuation_strategy_not_implemented"
    task_after = store.get_task(task.task_id)
    assert task_after is not None
    assert task_after.status == "needs_next_step"
