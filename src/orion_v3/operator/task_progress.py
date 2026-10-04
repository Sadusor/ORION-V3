from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import PurePosixPath
from typing import Any, Iterable

from orion_v3.state import EventType, OrionStateStore

from .control import OperatorControlDenied
from .result_grounding import verified_result_packet


class TaskProgressState(str, Enum):
    COMPLETED = "COMPLETED"
    NEEDS_NEXT_STEP = "NEEDS_NEXT_STEP"


@dataclass(frozen=True)
class TaskProgressDecision:
    task_id: str
    result_event_id: str
    decision_event_id: str
    state: TaskProgressState
    found_required_names: tuple[str, ...]
    missing_names: tuple[str, ...]
    duplicate: bool


def _normalize_names(values: Iterable[str]) -> tuple[str, ...]:
    names: list[str] = []
    seen: set[str] = set()
    for raw in values:
        value = str(raw or "").strip()
        if (
            not value
            or "/" in value
            or "\\" in value
            or value in {".", ".."}
        ):
            raise OperatorControlDenied(
                "invalid_completion_contract",
                "required_exact_names must contain safe basenames only.",
            )
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        names.append(value)
    if not names:
        raise OperatorControlDenied(
            "invalid_completion_contract",
            "required_exact_names must be non-empty.",
        )
    return tuple(names)


def _normalize_locations(values: Iterable[str]) -> tuple[str, ...]:
    locations: list[str] = []
    seen: set[str] = set()
    for raw in values:
        value = str(raw or "").strip().lower()
        if not value:
            continue
        if value in seen:
            continue
        seen.add(value)
        locations.append(value)
    if not locations:
        raise OperatorControlDenied(
            "invalid_completion_contract",
            "required_locations must be non-empty.",
        )
    return tuple(locations)


def decide_exact_search_task_progress(
    store: OrionStateStore,
    *,
    task_id: str,
    result_event_id: str,
    required_exact_names: Iterable[str],
    required_locations: Iterable[str],
) -> TaskProgressDecision:
    """Deterministically decide exact-search task progress from verified RESULT.

    The model does not participate in this state transition. ORION updates the
    task status and appends the causal DECISION atomically.
    """
    task = store.get_task(task_id)
    if task is None:
        raise OperatorControlDenied("unknown_task", "Task does not exist.")

    required_names = _normalize_names(required_exact_names)
    required_locations_tuple = _normalize_locations(required_locations)
    packet = verified_result_packet(
        store,
        task_id=task_id,
        result_event_id=result_event_id,
    )

    if packet.get("capability_id") != "fs.search_exact":
        raise OperatorControlDenied(
            "completion_contract_mismatch",
            "Exact-search completion requires fs.search_exact RESULT evidence.",
        )

    searched_locations = tuple(
        str(item).strip().lower()
        for item in packet.get("searched_locations", [])
        if str(item).strip()
    )
    if searched_locations != required_locations_tuple:
        raise OperatorControlDenied(
            "completion_scope_mismatch",
            "Verified search locations do not exactly match the completion contract.",
        )

    requested_keys = {name.casefold(): name for name in required_names}
    found_keys = {
        str(item.get("name") or "").casefold()
        for item in packet.get("matches", [])
        if isinstance(item, dict)
        and str(item.get("location") or "").strip().lower()
        in set(required_locations_tuple)
    }
    found_required = tuple(
        name for name in required_names if name.casefold() in found_keys
    )
    missing = tuple(
        name for name in required_names if name.casefold() not in found_keys
    )

    if not missing:
        state = TaskProgressState.COMPLETED
        reason = "all_required_exact_names_verified"
        task_status = "completed"
    else:
        state = TaskProgressState.NEEDS_NEXT_STEP
        reason = (
            "verified_search_incomplete_truncated"
            if bool(packet.get("truncated", False))
            else "required_exact_names_missing"
        )
        task_status = "needs_next_step"

    payload = {
        "kind": "exact_search_task_progress",
        "result_event_id": result_event_id,
        "action_sha256": packet["action_sha256"],
        "required_exact_names": list(required_names),
        "required_locations": list(required_locations_tuple),
        "found_required_names": list(found_required),
        "missing_names": list(missing),
        "verified_match_count": int(packet["match_count"]),
        "verified_result_truncated": bool(packet["truncated"]),
        "state": state.value,
        "reason": reason,
        "authority": "orion_deterministic_policy",
    }

    conn = store.connect()
    try:
        conn.execute("BEGIN IMMEDIATE")

        rows = conn.execute(
            """
            SELECT event_id,payload_json FROM events
            WHERE task_id=? AND parent_event_id=? AND event_type=?
            ORDER BY rowid ASC
            """,
            (task_id, result_event_id, EventType.DECISION.value),
        ).fetchall()
        for row in rows:
            existing_payload = json.loads(row["payload_json"])
            if existing_payload.get("kind") != "exact_search_task_progress":
                continue
            if existing_payload != payload:
                raise OperatorControlDenied(
                    "task_progress_conflict",
                    "A different task-progress decision already exists for this RESULT.",
                )
            conn.commit()
            return TaskProgressDecision(
                task_id=task_id,
                result_event_id=result_event_id,
                decision_event_id=row["event_id"],
                state=state,
                found_required_names=found_required,
                missing_names=missing,
                duplicate=True,
            )

        current_row = conn.execute(
            "SELECT status FROM tasks WHERE task_id=?",
            (task_id,),
        ).fetchone()
        if current_row is None:
            raise OperatorControlDenied("unknown_task", "Task does not exist.")
        current_status = str(current_row["status"])
        if current_status == "completed":
            raise OperatorControlDenied(
                "task_already_completed",
                "A completed task cannot be reopened by a later progress decision.",
            )

        result_event = store.get_event(result_event_id)
        if result_event is None:
            raise OperatorControlDenied("unknown_result", "RESULT event disappeared.")

        decision = store.append_event(
            task.project_id,
            EventType.DECISION,
            payload,
            actor_kind="orion",
            actor_id="deterministic-task-progress",
            task_id=task_id,
            parent_event_id=result_event_id,
            commit=False,
        )
        conn.execute(
            """
            UPDATE tasks
            SET status=?,updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
            WHERE task_id=?
            """,
            (task_status, task_id),
        )
        if conn.execute("SELECT changes()").fetchone()[0] != 1:
            raise OperatorControlDenied(
                "task_progress_update_failed",
                "Task status update did not affect exactly one task.",
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return TaskProgressDecision(
        task_id=task_id,
        result_event_id=result_event_id,
        decision_event_id=decision.event_id,
        state=state,
        found_required_names=found_required,
        missing_names=missing,
        duplicate=False,
    )


__all__ = [
    "TaskProgressDecision",
    "TaskProgressState",
    "decide_exact_search_task_progress",
]
