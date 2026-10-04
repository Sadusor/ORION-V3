from pathlib import Path

import pytest

from orion_v3.evidence import EvidenceEnvelope, Outcome
from orion_v3.operator import (
    ContinuationState,
    OperatorControlDenied,
    OperatorControlPlane,
    TaskProgressState,
    OWNER_RESUME_TOOL_NAME,
    apply_owner_scope_resume,
    decide_exact_search_continuation,
    decide_exact_search_task_progress,
    decide_resumed_exact_search_progress,
    dispatch_bound_owner_resumed_search,
    dispatch_owner_resumed_search,
    execute_read_only_proposal,
    owner_resume_governor_tool_spec,
    owner_resume_packet,
)
from orion_v3.state import EventType, OrionStateStore


MISSING = "__OWNER_RESUME_TARGET__.txt"


def make_waiting_owner(tmp_path: Path):
    store = OrionStateStore(tmp_path / "orion.db")
    store.initialize()
    project = store.create_project("Owner Resume", project_id="p-owner-resume")
    task = store.create_task(
        project.project_id,
        f"Find pyproject.toml and {MISSING}",
        task_id="t-owner-resume",
    )
    control = OperatorControlPlane(store)
    control.initialize()
    proposal = control.propose_capability_action(
        task.task_id,
        capability_id="fs.search_exact",
        params={
            "exact_names": ["pyproject.toml", MISSING],
            "locations": ["active_project"],
        },
        proposed_by="qwen35-9b-orion",
    )

    def initial_runner(task_id, params, trusted_roots):
        return (
            EvidenceEnvelope(
                task_id=task_id,
                lease_id="lease-initial",
                operation_id="filesystem.search",
                implementation_id="openjarvis.tool.orion_filesystem_search.v1",
                outcome=Outcome.CONFIRMED,
                result={
                    "operation_id": "filesystem.search",
                    "implementation_id": "openjarvis.tool.orion_filesystem_search.v1",
                    "searched_locations": ["active_project"],
                    "matches": [
                        {
                            "location": "active_project",
                            "relative_path": "pyproject.toml",
                            "name": "pyproject.toml",
                            "kind": "file",
                            "size_bytes": 10,
                            "modified_ns": 1,
                        }
                    ],
                    "match_count": 1,
                    "truncated": False,
                },
                verifier="orion.openjarvis.filesystem_search.v1",
            ),
            "lease-initial",
        )

    execution = execute_read_only_proposal(
        store,
        task_id=task.task_id,
        proposal_event_id=proposal.event_id,
        trusted_roots={"active_project": tmp_path},
        search_runner=initial_runner,
    )
    progress = decide_exact_search_task_progress(
        store,
        task_id=task.task_id,
        result_event_id=execution.result_event_id,
        required_exact_names=["pyproject.toml", MISSING],
        required_locations=["active_project"],
    )
    assert progress.state == TaskProgressState.NEEDS_NEXT_STEP
    continuation = decide_exact_search_continuation(
        store,
        task_id=task.task_id,
        progress_decision_event_id=progress.decision_event_id,
    )
    assert continuation.state == ContinuationState.OWNER_INPUT_REQUIRED
    return store, control, task, progress, continuation


def test_owner_scope_resume_is_append_only_atomic_and_idempotent(tmp_path: Path):
    store, _, task, _, continuation = make_waiting_owner(tmp_path)

    first = apply_owner_scope_resume(
        store,
        task_id=task.task_id,
        continuation_event_id=continuation.continuation_event_id,
        new_locations=["orion_artifacts"],
        owner_id="owner",
    )

    assert first.missing_names == (MISSING,)
    assert first.previous_locations == ("active_project",)
    assert first.new_locations == ("orion_artifacts",)
    assert first.effective_locations == ("active_project", "orion_artifacts")
    assert first.duplicate is False

    task_after = store.get_task(task.task_id)
    assert task_after is not None
    assert task_after.status == "queued"

    owner_event = store.get_event(first.owner_input_event_id)
    assert owner_event is not None
    assert owner_event.event_type == EventType.DECISION
    assert owner_event.parent_event_id == continuation.continuation_event_id
    assert owner_event.actor_kind == "owner"
    assert owner_event.payload["authority"] == "owner"
    assert owner_event.payload["automatic_retry_before_owner_input"] is False

    second = apply_owner_scope_resume(
        store,
        task_id=task.task_id,
        continuation_event_id=continuation.continuation_event_id,
        new_locations=["orion_artifacts"],
        owner_id="owner",
    )
    assert second.duplicate is True
    assert second.owner_input_event_id == first.owner_input_event_id


def test_owner_resume_cannot_repeat_exhausted_scope(tmp_path: Path):
    store, _, task, _, continuation = make_waiting_owner(tmp_path)

    with pytest.raises(OperatorControlDenied) as exc:
        apply_owner_scope_resume(
            store,
            task_id=task.task_id,
            continuation_event_id=continuation.continuation_event_id,
            new_locations=["active_project"],
        )

    assert exc.value.code == "owner_scope_not_new"
    task_after = store.get_task(task.task_id)
    assert task_after is not None
    assert task_after.status == "waiting_owner"


def test_owner_resume_packet_is_exact_and_model_safe(tmp_path: Path):
    store, _, task, _, continuation = make_waiting_owner(tmp_path)
    resumed = apply_owner_scope_resume(
        store,
        task_id=task.task_id,
        continuation_event_id=continuation.continuation_event_id,
        new_locations=["orion_artifacts"],
    )

    packet = owner_resume_packet(
        store,
        task_id=task.task_id,
        owner_input_event_id=resumed.owner_input_event_id,
    )

    assert packet == {
        "schema": "orion.v3.owner-resume-search.v0",
        "task_id": task.task_id,
        "owner_input_event_id": resumed.owner_input_event_id,
        "choice": "provide_new_search_scope",
        "missing_names": [MISSING],
        "new_locations": ["orion_artifacts"],
        "previous_locations": ["active_project"],
        "effective_authorized_locations": [
            "active_project",
            "orion_artifacts",
        ],
        "authority": "owner",
    }


def test_owner_resumed_governor_must_match_exact_amendment(tmp_path: Path):
    store, control, task, _, continuation = make_waiting_owner(tmp_path)
    resumed = apply_owner_scope_resume(
        store,
        task_id=task.task_id,
        continuation_event_id=continuation.continuation_event_id,
        new_locations=["orion_artifacts"],
    )
    packet = owner_resume_packet(
        store,
        task_id=task.task_id,
        owner_input_event_id=resumed.owner_input_event_id,
    )

    with pytest.raises(OperatorControlDenied) as exc:
        dispatch_owner_resumed_search(
            control,
            task_id=task.task_id,
            owner_resume=packet,
            tool_name="orion_capability_fs__search_exact",
            arguments={
                "exact_names": [MISSING, "another.txt"],
                "locations": ["orion_artifacts"],
            },
            actor_id="qwen35-9b-orion",
        )
    assert exc.value.code == "owner_resume_proposal_mismatch"

    with pytest.raises(OperatorControlDenied) as exc:
        dispatch_owner_resumed_search(
            control,
            task_id=task.task_id,
            owner_resume=packet,
            tool_name="orion_capability_fs__search_exact",
            arguments={
                "exact_names": [MISSING],
                "locations": ["active_project"],
            },
            actor_id="qwen35-9b-orion",
        )
    assert exc.value.code == "owner_resume_proposal_mismatch"


def test_owner_resumed_result_completes_from_cumulative_verified_evidence(tmp_path: Path):
    store, control, task, _, continuation = make_waiting_owner(tmp_path)
    resumed = apply_owner_scope_resume(
        store,
        task_id=task.task_id,
        continuation_event_id=continuation.continuation_event_id,
        new_locations=["orion_artifacts"],
    )
    packet = owner_resume_packet(
        store,
        task_id=task.task_id,
        owner_input_event_id=resumed.owner_input_event_id,
    )
    proposal = dispatch_owner_resumed_search(
        control,
        task_id=task.task_id,
        owner_resume=packet,
        tool_name="orion_capability_fs__search_exact",
        arguments={
            "exact_names": [MISSING],
            "locations": ["orion_artifacts"],
        },
        actor_id="qwen35-9b-orion",
    )
    proposal_event = store.get_event(proposal["event_id"])
    assert proposal_event is not None
    assert proposal_event.parent_event_id == resumed.owner_input_event_id

    def resumed_runner(task_id, params, trusted_roots):
        return (
            EvidenceEnvelope(
                task_id=task_id,
                lease_id="lease-resumed",
                operation_id="filesystem.search",
                implementation_id="openjarvis.tool.orion_filesystem_search.v1",
                outcome=Outcome.CONFIRMED,
                result={
                    "operation_id": "filesystem.search",
                    "implementation_id": "openjarvis.tool.orion_filesystem_search.v1",
                    "searched_locations": ["orion_artifacts"],
                    "matches": [
                        {
                            "location": "orion_artifacts",
                            "relative_path": MISSING,
                            "name": MISSING,
                            "kind": "file",
                            "size_bytes": 5,
                            "modified_ns": 2,
                        }
                    ],
                    "match_count": 1,
                    "truncated": False,
                },
                verifier="orion.openjarvis.filesystem_search.v1",
            ),
            "lease-resumed",
        )

    execution = execute_read_only_proposal(
        store,
        task_id=task.task_id,
        proposal_event_id=proposal["event_id"],
        trusted_roots={"orion_artifacts": tmp_path},
        search_runner=resumed_runner,
    )
    decision = decide_resumed_exact_search_progress(
        store,
        task_id=task.task_id,
        owner_input_event_id=resumed.owner_input_event_id,
        result_event_id=execution.result_event_id,
    )

    assert decision.state == "COMPLETED"
    assert decision.found_required_names == ("pyproject.toml", MISSING)
    assert decision.missing_names == ()

    task_after = store.get_task(task.task_id)
    assert task_after is not None
    assert task_after.status == "completed"

    event = store.get_event(decision.decision_event_id)
    assert event is not None
    assert event.parent_event_id == execution.result_event_id
    assert event.payload["required_exact_names"] == ["pyproject.toml", MISSING]
    assert event.payload["required_locations"] == [
        "active_project",
        "orion_artifacts",
    ]
    assert event.payload["owner_input_event_id"] == resumed.owner_input_event_id
    assert event.payload["authority"] == "orion_deterministic_policy"

    duplicate = decide_resumed_exact_search_progress(
        store,
        task_id=task.task_id,
        owner_input_event_id=resumed.owner_input_event_id,
        result_event_id=execution.result_event_id,
    )
    assert duplicate.duplicate is True
    assert duplicate.decision_event_id == decision.decision_event_id


def test_bound_owner_resume_tool_has_no_model_arguments(tmp_path: Path):
    store, _, task, _, continuation = make_waiting_owner(tmp_path)
    resumed = apply_owner_scope_resume(
        store,
        task_id=task.task_id,
        continuation_event_id=continuation.continuation_event_id,
        new_locations=["orion_artifacts"],
    )
    packet = owner_resume_packet(
        store,
        task_id=task.task_id,
        owner_input_event_id=resumed.owner_input_event_id,
    )

    tool = owner_resume_governor_tool_spec()
    assert tool["function"]["name"] == OWNER_RESUME_TOOL_NAME
    assert tool["function"]["parameters"] == {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }

    control = OperatorControlPlane(store)
    control.initialize()
    proposal = dispatch_bound_owner_resumed_search(
        control,
        task_id=task.task_id,
        owner_resume=packet,
        tool_name=OWNER_RESUME_TOOL_NAME,
        arguments={},
        actor_id="qwen35-9b-orion",
    )
    event = store.get_event(proposal["event_id"])
    assert event is not None
    assert event.parent_event_id == resumed.owner_input_event_id
    assert proposal["params"]["exact_names"] == [MISSING]
    assert proposal["params"]["locations"] == ["orion_artifacts"]

    with pytest.raises(OperatorControlDenied) as exc:
        dispatch_bound_owner_resumed_search(
            control,
            task_id=task.task_id,
            owner_resume=packet,
            tool_name=OWNER_RESUME_TOOL_NAME,
            arguments={"locations": ["active_project"]},
            actor_id="qwen35-9b-orion",
        )
    assert exc.value.code == "owner_resume_arguments_forbidden"
