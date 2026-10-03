from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from orion_v3.state import (
    EventType,
    MemoryKind,
    MemoryStatus,
    OrionStateStore,
    StateStoreError,
)


def make_store(tmp_path: Path) -> OrionStateStore:
    store = OrionStateStore(tmp_path / "orion-core.db")
    store.initialize()
    return store


def test_fresh_database_project_and_task_persist_across_reopen(tmp_path: Path):
    path = tmp_path / "orion-core.db"
    store = OrionStateStore(path)
    store.initialize()
    project = store.create_project("ORION", project_id="orion-v3")
    task = store.create_task(project.project_id, "Prove canonical memory", task_id="task-1")
    store.close()

    reopened = OrionStateStore(path)
    reopened.initialize()
    assert reopened.get_project("orion-v3") == project
    l0 = reopened.get_l0("orion-v3")
    assert l0["tasks"][0]["task_id"] == task.task_id
    assert l0["tasks"][0]["objective"] == "Prove canonical memory"


def test_event_payload_hash_is_canonical_and_deterministic(tmp_path: Path):
    store = make_store(tmp_path)
    project = store.create_project("ORION", project_id="p1")

    first = store.append_event(
        project.project_id,
        EventType.EVIDENCE,
        {"b": 2, "a": [3, 1]},
        actor_kind="test",
        actor_id="probe",
    )
    second = store.append_event(
        project.project_id,
        EventType.EVIDENCE,
        {"a": [3, 1], "b": 2},
        actor_kind="test",
        actor_id="probe",
    )

    canonical = json.dumps(
        {"a": [3, 1], "b": 2},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert first.payload_sha256 == expected
    assert second.payload_sha256 == expected


def test_events_are_physically_append_only(tmp_path: Path):
    store = make_store(tmp_path)
    project = store.create_project("ORION", project_id="p1")
    event = store.append_event(
        project.project_id,
        EventType.DECISION,
        {"decision": "Keep authority in ORION"},
        actor_kind="owner",
        actor_id="human",
    )

    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        store.connect().execute(
            "UPDATE events SET actor_id='tampered' WHERE event_id=?",
            (event.event_id,),
        )

    store.connect().rollback()

    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        store.connect().execute(
            "DELETE FROM events WHERE event_id=?",
            (event.event_id,),
        )


def test_parent_event_cannot_cross_project_boundary(tmp_path: Path):
    store = make_store(tmp_path)
    p1 = store.create_project("One", project_id="p1")
    p2 = store.create_project("Two", project_id="p2")
    parent = store.append_event(
        p1.project_id,
        EventType.PROPOSAL,
        {"proposal": "A"},
        actor_kind="ai",
        actor_id="reviewer",
    )
    with pytest.raises(StateStoreError, match="another project"):
        store.append_event(
            p2.project_id,
            EventType.REVIEW,
            {"review": "B"},
            actor_kind="ai",
            actor_id="critic",
            parent_event_id=parent.event_id,
        )


def test_memory_requires_real_same_project_source_event(tmp_path: Path):
    store = make_store(tmp_path)
    p1 = store.create_project("One", project_id="p1")
    p2 = store.create_project("Two", project_id="p2")
    source = store.append_event(
        p1.project_id,
        EventType.DECISION,
        {"decision": "Use semantic intent"},
        actor_kind="owner",
        actor_id="human",
    )

    with pytest.raises(StateStoreError, match="does not exist"):
        store.promote_memory(
            p1.project_id,
            MemoryKind.DECISION,
            "routing",
            "Semantic intent is canonical.",
            {"architecture": "intent->resolver"},
            source_event_id="missing",
            promoted_by="owner",
        )

    with pytest.raises(StateStoreError, match="another project"):
        store.promote_memory(
            p2.project_id,
            MemoryKind.DECISION,
            "routing",
            "Wrong project.",
            {"architecture": "bad"},
            source_event_id=source.event_id,
            promoted_by="owner",
        )


def test_memory_requires_explicit_supersession_and_preserves_history(tmp_path: Path):
    store = make_store(tmp_path)
    project = store.create_project("ORION", project_id="p1")
    first_event = store.append_event(
        project.project_id,
        EventType.DECISION,
        {"decision": "Qwen selects capability"},
        actor_kind="owner",
        actor_id="human",
    )
    first = store.promote_memory(
        project.project_id,
        MemoryKind.DECISION,
        "lightweight-routing",
        "Qwen selects semantic capability.",
        {"version": 1},
        source_event_id=first_event.event_id,
        promoted_by="owner",
    )
    assert first.status == MemoryStatus.CURRENT

    second_event = store.append_event(
        project.project_id,
        EventType.DECISION,
        {"decision": "Qwen emits semantic intent; ORION resolves"},
        actor_kind="owner",
        actor_id="human",
        parent_event_id=first_event.event_id,
    )

    with pytest.raises(StateStoreError, match="explicit supersession"):
        store.promote_memory(
            project.project_id,
            MemoryKind.DECISION,
            "lightweight-routing",
            "Qwen emits intent.",
            {"version": 2},
            source_event_id=second_event.event_id,
            promoted_by="owner",
        )

    second = store.promote_memory(
        project.project_id,
        MemoryKind.DECISION,
        "lightweight-routing",
        "Qwen emits semantic intent; ORION resolves capabilities.",
        {"version": 2},
        source_event_id=second_event.event_id,
        promoted_by="owner",
        supersedes_memory_id=first.memory_id,
    )
    assert second.status == MemoryStatus.CURRENT
    old = store.get_memory(first.memory_id)
    assert old is not None
    assert old.status == MemoryStatus.SUPERSEDED
    assert old.value == {"version": 1}

    l1 = store.get_l1(project.project_id)
    assert [item.memory_id for item in l1] == [second.memory_id]


def test_l0_l1_l2_are_project_scoped_and_provenance_backed(tmp_path: Path):
    store = make_store(tmp_path)
    p1 = store.create_project("ORION", project_id="orion")
    p2 = store.create_project("Other", project_id="other")
    store.create_task(p1.project_id, "Build memory", task_id="orion-task")
    store.create_task(p2.project_id, "Other work", task_id="other-task")

    decision_event = store.append_event(
        p1.project_id,
        EventType.DECISION,
        {"decision": "Memory is authoritative in SQLite"},
        actor_kind="owner",
        actor_id="human",
    )
    decision = store.promote_memory(
        p1.project_id,
        MemoryKind.DECISION,
        "memory-authority",
        "SQLite canonical state is authoritative.",
        {"authoritative": "sqlite"},
        source_event_id=decision_event.event_id,
        promoted_by="owner",
    )
    state_event = store.append_event(
        p1.project_id,
        EventType.RESULT,
        {"run": "V3-RUN-014", "result": "PASS"},
        actor_kind="verifier",
        actor_id="orion",
    )
    state = store.promote_memory(
        p1.project_id,
        MemoryKind.CURRENT_STATE,
        "latest-run",
        "V3-RUN-014 passed.",
        {"run": "V3-RUN-014"},
        source_event_id=state_event.event_id,
        promoted_by="owner",
    )

    foreign_event = store.append_event(
        p2.project_id,
        EventType.DECISION,
        {"decision": "foreign"},
        actor_kind="owner",
        actor_id="human",
    )
    store.promote_memory(
        p2.project_id,
        MemoryKind.DECISION,
        "foreign",
        "Must not leak.",
        {"foreign": True},
        source_event_id=foreign_event.event_id,
        promoted_by="owner",
    )

    l0 = store.get_l0(p1.project_id)
    assert l0["project"]["project_id"] == "orion"
    assert {task["task_id"] for task in l0["tasks"]} == {"orion-task"}
    assert {item["memory_id"] for item in l0["decisions"]} == {decision.memory_id}
    assert {item["memory_id"] for item in l0["current_state"]} == {state.memory_id}
    assert all("foreign" not in str(value) for value in l0.values())

    l1 = store.get_l1(
        p1.project_id,
        kinds=[MemoryKind.DECISION, MemoryKind.CURRENT_STATE],
        limit=10,
    )
    assert {item.memory_id for item in l1} == {decision.memory_id, state.memory_id}
    assert all(item.project_id == p1.project_id for item in l1)

    l2 = store.get_l2(p1.project_id, decision.memory_id)
    assert l2["memory"].memory_id == decision.memory_id
    assert l2["source_event"].event_id == decision_event.event_id
    assert l2["source_event"].payload == {
        "decision": "Memory is authoritative in SQLite"
    }


def test_l1_limit_is_bounded(tmp_path: Path):
    store = make_store(tmp_path)
    project = store.create_project("ORION", project_id="p1")
    for index in range(3):
        event = store.append_event(
            project.project_id,
            EventType.EVIDENCE,
            {"index": index},
            actor_kind="probe",
            actor_id="test",
        )
        store.promote_memory(
            project.project_id,
            MemoryKind.PROJECT_FACT,
            f"fact-{index}",
            f"Fact {index}",
            {"index": index},
            source_event_id=event.event_id,
            promoted_by="probe",
        )

    assert len(store.get_l1(project.project_id, limit=2)) == 2
    with pytest.raises(StateStoreError, match="between 1 and 100"):
        store.get_l1(project.project_id, limit=0)
