from pathlib import Path

import pytest

from orion_v3.evidence import EvidenceEnvelope, Outcome
from orion_v3.operator import (
    OperatorControlDenied,
    OperatorControlPlane,
    TaskProgressState,
    decide_exact_search_task_progress,
    execute_read_only_proposal,
)
from orion_v3.state import EventType, OrionStateStore


def make_result(tmp_path: Path, *, include_gateway: bool):
    store = OrionStateStore(tmp_path / ("orion-full.db" if include_gateway else "orion-partial.db"))
    store.initialize()
    project = store.create_project(
        "Progress",
        project_id="p-progress-full" if include_gateway else "p-progress-partial",
    )
    task = store.create_task(
        project.project_id,
        "Find pyproject.toml and gateway.py",
        task_id="t-progress-full" if include_gateway else "t-progress-partial",
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
                lease_id="lease-progress",
                operation_id="filesystem.search",
                implementation_id="openjarvis.tool.orion_filesystem_search.v1",
                outcome=Outcome.CONFIRMED,
                result={
                    "operation_id": "filesystem.search",
                    "implementation_id": "openjarvis.tool.orion_filesystem_search.v1",
                    "searched_locations": ["active_project"],
                    "matches": matches,
                    "match_count": len(matches),
                    "truncated": False,
                },
                verifier="orion.openjarvis.filesystem_search.v1",
            ),
            "lease-progress",
        )

    execution = execute_read_only_proposal(
        store,
        task_id=task.task_id,
        proposal_event_id=proposal.event_id,
        trusted_roots={"active_project": tmp_path},
        search_runner=runner,
    )
    return store, task, execution


def test_all_required_names_complete_task_atomically(tmp_path: Path):
    store, task, execution = make_result(tmp_path, include_gateway=True)

    decision = decide_exact_search_task_progress(
        store,
        task_id=task.task_id,
        result_event_id=execution.result_event_id,
        required_exact_names=["pyproject.toml", "gateway.py"],
        required_locations=["active_project"],
    )

    assert decision.state == TaskProgressState.COMPLETED
    assert decision.missing_names == ()
    assert decision.found_required_names == ("pyproject.toml", "gateway.py")
    assert decision.duplicate is False

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
    assert events[-1].parent_event_id == execution.result_event_id
    assert events[-1].payload["state"] == "COMPLETED"
    assert events[-1].payload["authority"] == "orion_deterministic_policy"


def test_missing_required_name_sets_needs_next_step(tmp_path: Path):
    store, task, execution = make_result(tmp_path, include_gateway=False)

    decision = decide_exact_search_task_progress(
        store,
        task_id=task.task_id,
        result_event_id=execution.result_event_id,
        required_exact_names=["pyproject.toml", "gateway.py"],
        required_locations=["active_project"],
    )

    assert decision.state == TaskProgressState.NEEDS_NEXT_STEP
    assert decision.found_required_names == ("pyproject.toml",)
    assert decision.missing_names == ("gateway.py",)

    task_after = store.get_task(task.task_id)
    assert task_after is not None
    assert task_after.status == "needs_next_step"


def test_progress_decision_is_idempotent_for_same_result(tmp_path: Path):
    store, task, execution = make_result(tmp_path, include_gateway=True)

    first = decide_exact_search_task_progress(
        store,
        task_id=task.task_id,
        result_event_id=execution.result_event_id,
        required_exact_names=["pyproject.toml", "gateway.py"],
        required_locations=["active_project"],
    )
    second = decide_exact_search_task_progress(
        store,
        task_id=task.task_id,
        result_event_id=execution.result_event_id,
        required_exact_names=["pyproject.toml", "gateway.py"],
        required_locations=["active_project"],
    )

    assert first.duplicate is False
    assert second.duplicate is True
    assert second.decision_event_id == first.decision_event_id

    events = store.list_task_events(task.project_id, task.task_id)
    assert [event.event_type for event in events].count(EventType.DECISION) == 1


def test_progress_scope_mismatch_fails_closed(tmp_path: Path):
    store, task, execution = make_result(tmp_path, include_gateway=True)

    with pytest.raises(OperatorControlDenied) as exc:
        decide_exact_search_task_progress(
            store,
            task_id=task.task_id,
            result_event_id=execution.result_event_id,
            required_exact_names=["pyproject.toml", "gateway.py"],
            required_locations=["documents"],
        )

    assert exc.value.code == "completion_scope_mismatch"
    task_after = store.get_task(task.task_id)
    assert task_after is not None
    assert task_after.status == "queued"


def test_completed_task_cannot_be_reopened_by_later_result(tmp_path: Path):
    store, task, execution = make_result(tmp_path, include_gateway=True)

    decide_exact_search_task_progress(
        store,
        task_id=task.task_id,
        result_event_id=execution.result_event_id,
        required_exact_names=["pyproject.toml", "gateway.py"],
        required_locations=["active_project"],
    )

    later = store.append_event(
        task.project_id,
        EventType.RESULT,
        {
            "kind": "routine_capability_result",
            "proposal_event_id": execution.proposal_event_id,
            "action_event_id": execution.action_event_id,
            "evidence_event_id": execution.evidence_event_id,
            "action_sha256": execution.action_sha256,
            "capability_id": execution.capability_id,
            "verification": dict(execution.verified_result),
        },
        actor_kind="orion",
        actor_id="later-result",
        task_id=task.task_id,
        parent_event_id=execution.evidence_event_id,
    )

    with pytest.raises(OperatorControlDenied) as exc:
        decide_exact_search_task_progress(
            store,
            task_id=task.task_id,
            result_event_id=later.event_id,
            required_exact_names=["pyproject.toml", "gateway.py"],
            required_locations=["active_project"],
        )

    assert exc.value.code == "task_already_completed"
