from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from orion_v3.state import EventType, OrionStateStore

from .control import OperatorControlDenied


class ContinuationState(str, Enum):
    COMPLETE_NO_ACTION = "COMPLETE_NO_ACTION"
    OWNER_INPUT_REQUIRED = "OWNER_INPUT_REQUIRED"


@dataclass(frozen=True)
class ContinuationDecision:
    task_id: str
    progress_decision_event_id: str
    continuation_event_id: str | None
    state: ContinuationState
    missing_names: tuple[str, ...]
    searched_locations: tuple[str, ...]
    duplicate: bool


def _require_progress_decision(
    store: OrionStateStore,
    *,
    task_id: str,
    progress_decision_event_id: str,
) -> tuple[Any, dict[str, Any]]:
    event = store.get_event(progress_decision_event_id)
    if event is None:
        raise OperatorControlDenied(
            "unknown_progress_decision",
            "Task-progress DECISION does not exist.",
        )
    if event.task_id != task_id:
        raise OperatorControlDenied(
            "wrong_task",
            "Task-progress DECISION belongs to another task.",
        )
    if event.event_type != EventType.DECISION:
        raise OperatorControlDenied(
            "invalid_progress_decision",
            "Continuation requires a task-progress DECISION event.",
        )
    payload = dict(event.payload)
    if payload.get("kind") != "exact_search_task_progress":
        raise OperatorControlDenied(
            "invalid_progress_decision",
            "DECISION is not an exact-search task-progress decision.",
        )
    if payload.get("authority") != "orion_deterministic_policy":
        raise OperatorControlDenied(
            "invalid_progress_authority",
            "Task-progress DECISION is not ORION deterministic policy.",
        )
    return event, payload


def decide_exact_search_continuation(
    store: OrionStateStore,
    *,
    task_id: str,
    progress_decision_event_id: str,
) -> ContinuationDecision:
    """Decide whether exact-search work may continue automatically.

    A completed task stops. A non-truncated exact search with required names
    still missing cannot gain evidence by blindly repeating the same bounded
    search, so ORION requires owner input instead of looping autonomously.
    """
    task = store.get_task(task_id)
    if task is None:
        raise OperatorControlDenied("unknown_task", "Task does not exist.")

    progress_event, payload = _require_progress_decision(
        store,
        task_id=task_id,
        progress_decision_event_id=progress_decision_event_id,
    )

    progress_state = str(payload.get("state") or "")
    missing_names = tuple(str(x) for x in payload.get("missing_names") or [])
    required_locations = tuple(
        str(x) for x in payload.get("required_locations") or []
    )
    truncated = bool(payload.get("verified_result_truncated", False))

    if progress_state == "COMPLETED":
        if task.status != "completed":
            raise OperatorControlDenied(
                "task_progress_status_mismatch",
                "COMPLETED decision does not match canonical task status.",
            )
        return ContinuationDecision(
            task_id=task_id,
            progress_decision_event_id=progress_event.event_id,
            continuation_event_id=None,
            state=ContinuationState.COMPLETE_NO_ACTION,
            missing_names=(),
            searched_locations=required_locations,
            duplicate=False,
        )

    if progress_state != "NEEDS_NEXT_STEP":
        raise OperatorControlDenied(
            "unsupported_progress_state",
            "Continuation policy does not recognize this task-progress state.",
        )
    if task.status not in {"needs_next_step", "waiting_owner"}:
        raise OperatorControlDenied(
            "task_progress_status_mismatch",
            "NEEDS_NEXT_STEP decision does not match canonical task status.",
        )
    if not missing_names:
        raise OperatorControlDenied(
            "invalid_progress_decision",
            "NEEDS_NEXT_STEP decision has no missing requirement.",
        )
    if truncated:
        raise OperatorControlDenied(
            "continuation_strategy_not_implemented",
            "Truncated exact-search continuation requires an explicit bounded strategy.",
        )

    continuation_payload = {
        "kind": "task_continuation",
        "progress_decision_event_id": progress_event.event_id,
        "source_result_event_id": progress_event.parent_event_id,
        "state": ContinuationState.OWNER_INPUT_REQUIRED.value,
        "reason": "non_truncated_exact_search_missing_required_names",
        "missing_names": list(missing_names),
        "searched_locations": list(required_locations),
        "owner_choices": [
            "provide_new_search_scope",
            "provide_expected_location",
            "stop_task",
        ],
        "automatic_retry_allowed": False,
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
            (
                task_id,
                progress_event.event_id,
                EventType.DECISION.value,
            ),
        ).fetchall()
        for row in rows:
            existing_payload = json.loads(row["payload_json"])
            if existing_payload.get("kind") != "task_continuation":
                continue
            if existing_payload != continuation_payload:
                raise OperatorControlDenied(
                    "continuation_conflict",
                    "A different continuation decision already exists.",
                )
            conn.commit()
            return ContinuationDecision(
                task_id=task_id,
                progress_decision_event_id=progress_event.event_id,
                continuation_event_id=row["event_id"],
                state=ContinuationState.OWNER_INPUT_REQUIRED,
                missing_names=missing_names,
                searched_locations=required_locations,
                duplicate=True,
            )

        continuation = store.append_event(
            task.project_id,
            EventType.DECISION,
            continuation_payload,
            actor_kind="orion",
            actor_id="deterministic-continuation-policy",
            task_id=task_id,
            parent_event_id=progress_event.event_id,
            commit=False,
        )
        conn.execute(
            """
            UPDATE tasks SET
                status='waiting_owner',
                updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
            WHERE task_id=? AND status='needs_next_step'
            """,
            (task_id,),
        )
        if conn.execute("SELECT changes()").fetchone()[0] != 1:
            raise OperatorControlDenied(
                "continuation_status_update_failed",
                "Task did not transition exactly once into waiting_owner.",
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return ContinuationDecision(
        task_id=task_id,
        progress_decision_event_id=progress_event.event_id,
        continuation_event_id=continuation.event_id,
        state=ContinuationState.OWNER_INPUT_REQUIRED,
        missing_names=missing_names,
        searched_locations=required_locations,
        duplicate=False,
    )


def owner_input_packet(
    store: OrionStateStore,
    *,
    task_id: str,
    continuation_event_id: str,
) -> dict[str, Any]:
    """Build a model-safe packet for asking the owner what to do next."""
    event = store.get_event(continuation_event_id)
    if event is None:
        raise OperatorControlDenied(
            "unknown_continuation",
            "Continuation DECISION does not exist.",
        )
    if event.task_id != task_id or event.event_type != EventType.DECISION:
        raise OperatorControlDenied(
            "invalid_continuation",
            "Continuation DECISION identity is invalid.",
        )
    payload = dict(event.payload)
    if payload.get("kind") != "task_continuation":
        raise OperatorControlDenied(
            "invalid_continuation",
            "DECISION is not a task-continuation decision.",
        )
    if payload.get("state") != ContinuationState.OWNER_INPUT_REQUIRED.value:
        raise OperatorControlDenied(
            "invalid_continuation",
            "Continuation does not require owner input.",
        )
    if payload.get("authority") != "orion_deterministic_policy":
        raise OperatorControlDenied(
            "invalid_continuation_authority",
            "Continuation authority is not ORION deterministic policy.",
        )
    task = store.get_task(task_id)
    if task is None or task.status != "waiting_owner":
        raise OperatorControlDenied(
            "continuation_status_mismatch",
            "Canonical task is not waiting for owner input.",
        )

    return {
        "schema": "orion.v3.owner-input-required.v0",
        "task_id": task_id,
        "continuation_event_id": event.event_id,
        "state": "OWNER_INPUT_REQUIRED",
        "missing_names": list(payload.get("missing_names") or []),
        "searched_locations": list(payload.get("searched_locations") or []),
        "owner_choices": list(payload.get("owner_choices") or []),
        "automatic_retry_allowed": False,
        "authority": "orion_deterministic_policy",
    }


__all__ = [
    "ContinuationDecision",
    "ContinuationState",
    "decide_exact_search_continuation",
    "owner_input_packet",
]
