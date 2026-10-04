from pathlib import Path

import pytest

from orion_v3.evidence import EvidenceEnvelope, Outcome
from orion_v3.operator import (
    OperatorControlDenied,
    OperatorControlPlane,
    execute_read_only_proposal,
    verified_result_packet,
)
from orion_v3.state import EventType, OrionStateStore


def make_verified_result(tmp_path: Path):
    store = OrionStateStore(tmp_path / "orion.db")
    store.initialize()
    project = store.create_project("Grounding", project_id="p-ground")
    task = store.create_task(
        project.project_id,
        "Find files",
        task_id="t-ground",
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

    def runner(task_id, params, trusted_roots):
        return (
            EvidenceEnvelope(
                task_id=task_id,
                lease_id="lease-ground",
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
                        },
                        {
                            "location": "active_project",
                            "relative_path": "src/orion_v3/authority/gateway.py",
                            "name": "gateway.py",
                            "kind": "file",
                            "size_bytes": 20,
                            "modified_ns": 2,
                        },
                    ],
                    "match_count": 2,
                    "truncated": False,
                },
                verifier="orion.openjarvis.filesystem_search.v1",
            ),
            "lease-ground",
        )

    execution = execute_read_only_proposal(
        store,
        task_id=task.task_id,
        proposal_event_id=proposal.event_id,
        trusted_roots={"active_project": tmp_path},
        search_runner=runner,
    )
    return store, task, execution


def test_verified_result_packet_exposes_only_verified_relative_evidence(tmp_path: Path):
    store, task, execution = make_verified_result(tmp_path)

    packet = verified_result_packet(
        store,
        task_id=task.task_id,
        result_event_id=execution.result_event_id,
    )

    assert packet["schema"] == "orion.v3.verified-result-packet.v0"
    assert packet["verification_status"] == "PASS"
    assert packet["authority"] == "verified_evidence_only"
    assert packet["capability_id"] == "fs.search_exact"
    assert packet["match_count"] == 2
    assert packet["found_names"] == ["gateway.py", "pyproject.toml"]
    assert [item["relative_path"] for item in packet["matches"]] == [
        "pyproject.toml",
        "src/orion_v3/authority/gateway.py",
    ]
    encoded = repr(packet)
    assert str(tmp_path) not in encoded
    assert "lease-ground" not in encoded
    assert "size_bytes" not in encoded
    assert "modified_ns" not in encoded


def test_verified_result_packet_rejects_non_result_event(tmp_path: Path):
    store, task, execution = make_verified_result(tmp_path)
    with pytest.raises(OperatorControlDenied) as exc:
        verified_result_packet(
            store,
            task_id=task.task_id,
            result_event_id=execution.evidence_event_id,
        )
    assert exc.value.code == "invalid_result_event"


def test_verified_result_packet_rejects_wrong_task(tmp_path: Path):
    store, task, execution = make_verified_result(tmp_path)
    store.create_task(
        task.project_id,
        "Other task",
        task_id="other-task",
    )
    with pytest.raises(OperatorControlDenied) as exc:
        verified_result_packet(
            store,
            task_id="other-task",
            result_event_id=execution.result_event_id,
        )
    assert exc.value.code == "wrong_task"


def test_verified_result_packet_rejects_broken_lineage(tmp_path: Path):
    store, task, execution = make_verified_result(tmp_path)
    bad = store.append_event(
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
        actor_id="forged-result",
        task_id=task.task_id,
        parent_event_id=execution.action_event_id,
    )

    with pytest.raises(OperatorControlDenied) as exc:
        verified_result_packet(
            store,
            task_id=task.task_id,
            result_event_id=bad.event_id,
        )
    assert exc.value.code == "broken_result_lineage"
