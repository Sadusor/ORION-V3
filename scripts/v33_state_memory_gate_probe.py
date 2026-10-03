from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
from pathlib import Path

from orion_v3.state import (
    EventType,
    MemoryKind,
    MemoryStatus,
    OrionStateStore,
    StateStoreError,
)


def main() -> int:
    print("V3_RUN_ID> V3-RUN-015")
    print("CANONICAL_STATE_MEMORY_GATE> START")
    with tempfile.TemporaryDirectory(prefix="orion-v3-state-") as temp:
        path = Path(temp) / "orion-core.db"
        store = OrionStateStore(path)
        store.initialize()
        print("DB_INIT> PASS")

        orion = store.create_project("ORION", project_id="orion")
        other = store.create_project("Other", project_id="other")
        store.create_task(orion.project_id, "Prove state and memory", task_id="task-orion")
        store.create_task(other.project_id, "Foreign task", task_id="task-other")
        print("PROJECT_TASK_PERSISTENCE_SETUP> PASS")

        one = store.append_event(
            orion.project_id,
            EventType.EVIDENCE,
            {"b": 2, "a": [3, 1]},
            actor_kind="probe",
            actor_id="run-015",
            task_id="task-orion",
        )
        two = store.append_event(
            orion.project_id,
            EventType.EVIDENCE,
            {"a": [3, 1], "b": 2},
            actor_kind="probe",
            actor_id="run-015",
        )
        canonical = json.dumps(
            {"a": [3, 1], "b": 2},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        expected_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        assert one.payload_sha256 == expected_hash == two.payload_sha256
        print("DETERMINISTIC_EVENT_HASH> PASS")

        try:
            store.connect().execute(
                "UPDATE events SET actor_id='changed' WHERE event_id=?",
                (one.event_id,),
            )
        except sqlite3.IntegrityError:
            store.connect().rollback()
        else:
            raise AssertionError("event UPDATE unexpectedly succeeded")
        try:
            store.connect().execute(
                "DELETE FROM events WHERE event_id=?",
                (one.event_id,),
            )
        except sqlite3.IntegrityError:
            store.connect().rollback()
        else:
            raise AssertionError("event DELETE unexpectedly succeeded")
        print("EVENT_APPEND_ONLY_TRIGGER> PASS")

        foreign_parent = store.append_event(
            other.project_id,
            EventType.PROPOSAL,
            {"proposal": "foreign"},
            actor_kind="probe",
            actor_id="run-015",
        )
        try:
            store.append_event(
                orion.project_id,
                EventType.REVIEW,
                {"review": "must fail"},
                actor_kind="probe",
                actor_id="run-015",
                parent_event_id=foreign_parent.event_id,
            )
        except StateStoreError:
            pass
        else:
            raise AssertionError("cross-project parent event unexpectedly accepted")
        print("CROSS_PROJECT_EVENT_PARENT> DENIED")

        try:
            store.promote_memory(
                orion.project_id,
                MemoryKind.DECISION,
                "routing",
                "Missing provenance",
                {"bad": True},
                source_event_id="missing",
                promoted_by="owner",
            )
        except StateStoreError:
            pass
        else:
            raise AssertionError("memory without source event unexpectedly promoted")
        print("MEMORY_WITHOUT_PROVENANCE> DENIED")

        try:
            store.promote_memory(
                orion.project_id,
                MemoryKind.DECISION,
                "routing",
                "Foreign provenance",
                {"bad": True},
                source_event_id=foreign_parent.event_id,
                promoted_by="owner",
            )
        except StateStoreError:
            pass
        else:
            raise AssertionError("cross-project memory provenance unexpectedly accepted")
        print("CROSS_PROJECT_MEMORY_PROVENANCE> DENIED")

        first_decision_event = store.append_event(
            orion.project_id,
            EventType.DECISION,
            {"decision": "Qwen emits semantic intent"},
            actor_kind="owner",
            actor_id="human",
            task_id="task-orion",
        )
        first_memory = store.promote_memory(
            orion.project_id,
            MemoryKind.DECISION,
            "lightweight-routing",
            "Qwen emits semantic intent; ORION owns resolution.",
            {"version": 1, "resolver": "orion"},
            source_event_id=first_decision_event.event_id,
            promoted_by="owner",
        )
        assert first_memory.status == MemoryStatus.CURRENT
        print("FIRST_MEMORY_PROMOTION> PASS")

        second_decision_event = store.append_event(
            orion.project_id,
            EventType.DECISION,
            {"decision": "Add deterministic canonicalizer before resolver"},
            actor_kind="owner",
            actor_id="human",
            parent_event_id=first_decision_event.event_id,
        )
        try:
            store.promote_memory(
                orion.project_id,
                MemoryKind.DECISION,
                "lightweight-routing",
                "Silent overwrite must fail.",
                {"version": 2},
                source_event_id=second_decision_event.event_id,
                promoted_by="owner",
            )
        except StateStoreError:
            pass
        else:
            raise AssertionError("silent current-memory overwrite unexpectedly accepted")
        print("MEMORY_SILENT_OVERWRITE> DENIED")

        second_memory = store.promote_memory(
            orion.project_id,
            MemoryKind.DECISION,
            "lightweight-routing",
            "Qwen literal semantics -> ORION canonicalizer -> resolver.",
            {"version": 2, "canonicalizer": True},
            source_event_id=second_decision_event.event_id,
            promoted_by="owner",
            supersedes_memory_id=first_memory.memory_id,
        )
        old = store.get_memory(first_memory.memory_id)
        assert old is not None and old.status == MemoryStatus.SUPERSEDED
        assert second_memory.status == MemoryStatus.CURRENT
        print("EXPLICIT_MEMORY_SUPERSESSION> PASS")

        result_event = store.append_event(
            orion.project_id,
            EventType.RESULT,
            {"run": "V3-RUN-014", "result": "PASS"},
            actor_kind="verifier",
            actor_id="orion",
            task_id="task-orion",
        )
        state_memory = store.promote_memory(
            orion.project_id,
            MemoryKind.CURRENT_STATE,
            "latest-governor-gate",
            "V3-RUN-014 owner-observed physical PASS.",
            {"run": "V3-RUN-014", "status": "PASS"},
            source_event_id=result_event.event_id,
            promoted_by="owner",
        )

        other_event = store.append_event(
            other.project_id,
            EventType.DECISION,
            {"decision": "foreign must not leak"},
            actor_kind="owner",
            actor_id="human",
        )
        foreign_memory = store.promote_memory(
            other.project_id,
            MemoryKind.DECISION,
            "foreign",
            "Foreign memory.",
            {"foreign": True},
            source_event_id=other_event.event_id,
            promoted_by="owner",
        )

        l0 = store.get_l0(orion.project_id)
        assert l0["project"]["project_id"] == "orion"
        assert {task["task_id"] for task in l0["tasks"]} == {"task-orion"}
        serialized_l0 = json.dumps(l0, ensure_ascii=False, sort_keys=True)
        assert foreign_memory.memory_id not in serialized_l0
        assert "task-other" not in serialized_l0
        print("L0_PROJECT_SCOPE> PASS")

        l1 = store.get_l1(
            orion.project_id,
            kinds=[MemoryKind.DECISION, MemoryKind.CURRENT_STATE],
            limit=10,
        )
        assert {item.memory_id for item in l1} == {
            second_memory.memory_id,
            state_memory.memory_id,
        }
        assert all(item.project_id == "orion" for item in l1)
        print("L1_CURRENT_CANONICAL_SCOPE> PASS")

        l2 = store.get_l2(orion.project_id, second_memory.memory_id)
        assert l2["source_event"].event_id == second_decision_event.event_id
        assert l2["source_event"].payload == {
            "decision": "Add deterministic canonicalizer before resolver"
        }
        assert l2["parent_event"].event_id == first_decision_event.event_id
        print("L2_PROVENANCE_EXPANSION> PASS")

        store.close()
        reopened = OrionStateStore(path)
        reopened.initialize()
        assert reopened.get_project("orion") is not None
        reopened_second = reopened.get_memory(second_memory.memory_id)
        assert reopened_second is not None
        assert reopened_second.status == MemoryStatus.CURRENT
        assert reopened.get_event(second_decision_event.event_id) is not None
        print("CLOSE_REOPEN_PERSISTENCE> PASS")

        print("NETWORK_MODEL_DEPENDENCY> NONE")
        print("CANONICAL_STATE_MEMORY_GATE> PASS")
        print("STATUS> PASS")
        reopened.close()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
