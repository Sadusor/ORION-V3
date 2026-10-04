from pathlib import Path

import pytest

from orion_v3.evidence import EvidenceEnvelope, Outcome
from orion_v3.operator import (
    OperatorControlDenied,
    OperatorControlPlane,
    execute_read_only_proposal,
)
from orion_v3.state import EventType, OrionStateStore


def make_control(tmp_path: Path):
    store = OrionStateStore(tmp_path / "orion.db")
    store.initialize()
    project = store.create_project("Routine Execution", project_id="p-exec")
    task = store.create_task(
        project.project_id,
        "Find README.md",
        task_id="t-exec",
    )
    control = OperatorControlPlane(store)
    control.initialize()
    return store, control, task


def confirmed_search_runner(task_id, params, trusted_roots):
    assert task_id == "t-exec"
    assert params["exact_names"] == ["README.md"]
    assert params["locations"] == ["active_project"]
    assert "active_project" in trusted_roots
    return (
        EvidenceEnvelope(
            task_id=task_id,
            lease_id="lease-test",
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
                        "relative_path": "README.md",
                        "name": "README.md",
                        "kind": "file",
                        "size_bytes": 12,
                        "modified_ns": 1,
                    }
                ],
                "match_count": 1,
                "truncated": False,
            },
            verifier="orion.openjarvis.filesystem_search.v1",
        ),
        "lease-test",
    )


def test_read_only_proposal_executes_from_canonical_event_and_builds_causal_chain(tmp_path: Path):
    store, control, task = make_control(tmp_path)

    proposal = control.propose_capability_action(
        task.task_id,
        capability_id="fs.search_exact",
        params={
            "exact_names": ["README.md"],
            "locations": ["active_project"],
        },
        proposed_by="qwen35-9b-orion",
    )

    result = execute_read_only_proposal(
        store,
        task_id=task.task_id,
        proposal_event_id=proposal.event_id,
        trusted_roots={"active_project": tmp_path},
        search_runner=confirmed_search_runner,
    )

    assert result.capability_id == "fs.search_exact"
    assert result.action_sha256 == proposal.action.action_sha256
    assert result.evidence.outcome == Outcome.CONFIRMED
    assert result.verified_result["status"] == "PASS"
    assert result.verified_result["found_names"] == ["README.md"]

    events = store.list_task_events(task.project_id, task.task_id)
    assert [event.event_type for event in events] == [
        EventType.PROPOSAL,
        EventType.ACTION,
        EventType.EVIDENCE,
        EventType.RESULT,
    ]
    assert events[1].parent_event_id == events[0].event_id
    assert events[2].parent_event_id == events[1].event_id
    assert events[3].parent_event_id == events[2].event_id
    assert events[3].payload["verification"]["status"] == "PASS"


def test_non_read_only_proposal_cannot_use_routine_auto_dispatch(tmp_path: Path):
    store, control, task = make_control(tmp_path)

    proposal = control.propose_capability_action(
        task.task_id,
        capability_id="fs.reveal",
        params={
            "location": "active_project",
            "relative_path": ".",
        },
        proposed_by="qwen35-9b-orion",
    )

    called = False

    def runner(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("Hand must not execute")

    with pytest.raises(OperatorControlDenied) as exc:
        execute_read_only_proposal(
            store,
            task_id=task.task_id,
            proposal_event_id=proposal.event_id,
            trusted_roots={"active_project": tmp_path},
            search_runner=runner,
        )

    assert exc.value.code == "routine_auto_dispatch_forbidden"
    assert called is False


def test_bad_hash_proposal_is_denied_before_hand(tmp_path: Path):
    store, _, task = make_control(tmp_path)

    event = store.append_event(
        task.project_id,
        EventType.PROPOSAL,
        {
            "kind": "capability_action_proposed",
            "action_sha256": "not-the-real-hash",
            "action": {
                "capability_id": "fs.search_exact",
                "capability_version": 2,
                "params": {
                    "exact_names": ["README.md"],
                    "locations": ["active_project"],
                    "recursive": True,
                    "max_depth": 4,
                    "max_results": 50,
                    "reveal_containing_folders": False,
                },
            },
        },
        actor_kind="local_operator",
        actor_id="qwen35-9b-orion",
        task_id=task.task_id,
    )

    called = False

    def runner(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("Hand must not execute")

    with pytest.raises(OperatorControlDenied) as exc:
        execute_read_only_proposal(
            store,
            task_id=task.task_id,
            proposal_event_id=event.event_id,
            trusted_roots={"active_project": tmp_path},
            search_runner=runner,
        )

    assert exc.value.code == "proposal_tamper_detected"
    assert called is False


def test_evidence_scope_mismatch_fails_before_result(tmp_path: Path):
    store, control, task = make_control(tmp_path)

    proposal = control.propose_capability_action(
        task.task_id,
        capability_id="fs.search_exact",
        params={
            "exact_names": ["README.md"],
            "locations": ["active_project"],
        },
        proposed_by="qwen35-9b-orion",
    )

    def bad_runner(task_id, params, trusted_roots):
        return (
            EvidenceEnvelope(
                task_id=task_id,
                lease_id="lease-bad",
                operation_id="filesystem.search",
                implementation_id="openjarvis.tool.orion_filesystem_search.v1",
                outcome=Outcome.CONFIRMED,
                result={
                    "operation_id": "filesystem.search",
                    "implementation_id": "openjarvis.tool.orion_filesystem_search.v1",
                    "searched_locations": ["desktop"],
                    "matches": [],
                    "match_count": 0,
                    "truncated": False,
                },
                verifier="orion.openjarvis.filesystem_search.v1",
            ),
            "lease-bad",
        )

    with pytest.raises(OperatorControlDenied) as exc:
        execute_read_only_proposal(
            store,
            task_id=task.task_id,
            proposal_event_id=proposal.event_id,
            trusted_roots={"active_project": tmp_path},
            search_runner=bad_runner,
        )

    assert exc.value.code == "hand_evidence_scope_mismatch"
    events = store.list_task_events(task.project_id, task.task_id)
    assert [event.event_type for event in events] == [
        EventType.PROPOSAL,
        EventType.ACTION,
        EventType.EVIDENCE,
    ]
    assert all(event.event_type != EventType.RESULT for event in events)


def test_read_only_proposal_cannot_be_dispatched_twice(tmp_path: Path):
    store, control, task = make_control(tmp_path)

    proposal = control.propose_capability_action(
        task.task_id,
        capability_id="fs.search_exact",
        params={
            "exact_names": ["README.md"],
            "locations": ["active_project"],
        },
        proposed_by="qwen35-9b-orion",
    )

    execute_read_only_proposal(
        store,
        task_id=task.task_id,
        proposal_event_id=proposal.event_id,
        trusted_roots={"active_project": tmp_path},
        search_runner=confirmed_search_runner,
    )

    with pytest.raises(OperatorControlDenied) as exc:
        execute_read_only_proposal(
            store,
            task_id=task.task_id,
            proposal_event_id=proposal.event_id,
            trusted_roots={"active_project": tmp_path},
            search_runner=confirmed_search_runner,
        )

    assert exc.value.code == "proposal_already_dispatched"
