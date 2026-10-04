from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping

from orion_v3.capabilities import inherited_registry_v0
from orion_v3.state import EventType, OrionStateStore

from .control import OperatorControlDenied, OperatorControlPlane
from .result_grounding import verified_result_packet


OWNER_RESUME_TOOL_NAME = "orion_continue_owner_authorized_search"


class OwnerResumeChoice(str, Enum):
    PROVIDE_NEW_SEARCH_SCOPE = "provide_new_search_scope"


@dataclass(frozen=True)
class OwnerScopeResume:
    task_id: str
    continuation_event_id: str
    owner_input_event_id: str
    missing_names: tuple[str, ...]
    previous_locations: tuple[str, ...]
    new_locations: tuple[str, ...]
    effective_locations: tuple[str, ...]
    duplicate: bool


@dataclass(frozen=True)
class ResumedProgressDecision:
    task_id: str
    result_event_id: str
    decision_event_id: str
    state: str
    found_required_names: tuple[str, ...]
    missing_names: tuple[str, ...]
    duplicate: bool


def _clean_unique(values: Iterable[str], *, field: str) -> tuple[str, ...]:
    output: list[str] = []
    seen: set[str] = set()
    for raw in values:
        value = str(raw or "").strip()
        if not value:
            raise OperatorControlDenied(
                "invalid_owner_resume",
                field + " contains an empty value.",
            )
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        output.append(value)
    if not output:
        raise OperatorControlDenied(
            "invalid_owner_resume",
            field + " must be non-empty.",
        )
    return tuple(output)


def _require_continuation(
    store: OrionStateStore,
    *,
    task_id: str,
    continuation_event_id: str,
) -> tuple[Any, dict[str, Any]]:
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
    if payload.get("state") != "OWNER_INPUT_REQUIRED":
        raise OperatorControlDenied(
            "invalid_continuation",
            "Continuation is not waiting for owner input.",
        )
    if payload.get("authority") != "orion_deterministic_policy":
        raise OperatorControlDenied(
            "invalid_continuation_authority",
            "Continuation authority is not ORION deterministic policy.",
        )
    if payload.get("automatic_retry_allowed") is not False:
        raise OperatorControlDenied(
            "invalid_continuation",
            "Continuation unexpectedly permits automatic retry.",
        )
    return event, payload


def apply_owner_scope_resume(
    store: OrionStateStore,
    *,
    task_id: str,
    continuation_event_id: str,
    new_locations: Iterable[str],
    owner_id: str = "owner",
) -> OwnerScopeResume:
    """Record one explicit owner scope extension for a waiting task.

    The prior completion contract remains append-only. This owner event adds one
    exact scope amendment; it does not rewrite prior RESULT/DECISION history.
    """
    task = store.get_task(task_id)
    if task is None:
        raise OperatorControlDenied("unknown_task", "Task does not exist.")

    continuation, continuation_payload = _require_continuation(
        store,
        task_id=task_id,
        continuation_event_id=continuation_event_id,
    )
    missing_names = _clean_unique(
        continuation_payload.get("missing_names") or [],
        field="missing_names",
    )
    previous_locations = _clean_unique(
        continuation_payload.get("searched_locations") or [],
        field="searched_locations",
    )
    requested_new = _clean_unique(new_locations, field="new_locations")

    # Reuse the semantic registry to validate named roots. Hidden execution
    # defaults remain ORION-owned and are not accepted from owner/model here.
    search_definition = inherited_registry_v0().get("fs.search_exact")
    normalized = search_definition.normalize_params(
        {
            "exact_names": list(missing_names),
            "locations": list(requested_new),
        }
    )
    validated_new = tuple(str(x) for x in normalized["locations"])

    overlap = {
        location.casefold() for location in previous_locations
    } & {
        location.casefold() for location in validated_new
    }
    if overlap:
        raise OperatorControlDenied(
            "owner_scope_not_new",
            "Owner resume scope must add a new named location, not repeat an exhausted one.",
        )

    effective = tuple([*previous_locations, *validated_new])
    payload = {
        "kind": "owner_continuation_input",
        "choice": OwnerResumeChoice.PROVIDE_NEW_SEARCH_SCOPE.value,
        "continuation_event_id": continuation.event_id,
        "progress_decision_event_id": continuation.parent_event_id,
        "missing_names": list(missing_names),
        "previous_locations": list(previous_locations),
        "new_locations": list(validated_new),
        "effective_authorized_locations": list(effective),
        "automatic_retry_before_owner_input": False,
        "authority": "owner",
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
            (task_id, continuation.event_id, EventType.DECISION.value),
        ).fetchall()
        for row in rows:
            existing_payload = json.loads(row["payload_json"])
            if existing_payload.get("kind") != "owner_continuation_input":
                continue
            if existing_payload != payload:
                raise OperatorControlDenied(
                    "owner_resume_conflict",
                    "A different owner continuation input already exists.",
                )
            conn.commit()
            return OwnerScopeResume(
                task_id=task_id,
                continuation_event_id=continuation.event_id,
                owner_input_event_id=row["event_id"],
                missing_names=missing_names,
                previous_locations=previous_locations,
                new_locations=validated_new,
                effective_locations=effective,
                duplicate=True,
            )

        current = conn.execute(
            "SELECT status FROM tasks WHERE task_id=?",
            (task_id,),
        ).fetchone()
        if current is None:
            raise OperatorControlDenied("unknown_task", "Task does not exist.")
        if str(current["status"]) != "waiting_owner":
            raise OperatorControlDenied(
                "owner_resume_status_mismatch",
                "Task is not waiting for owner input.",
            )

        owner_event = store.append_event(
            task.project_id,
            EventType.DECISION,
            payload,
            actor_kind="owner",
            actor_id=str(owner_id or "owner"),
            task_id=task_id,
            parent_event_id=continuation.event_id,
            commit=False,
        )
        conn.execute(
            """
            UPDATE tasks SET
                status='queued',
                updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
            WHERE task_id=? AND status='waiting_owner'
            """,
            (task_id,),
        )
        if conn.execute("SELECT changes()").fetchone()[0] != 1:
            raise OperatorControlDenied(
                "owner_resume_status_update_failed",
                "Task did not transition exactly once out of waiting_owner.",
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return OwnerScopeResume(
        task_id=task_id,
        continuation_event_id=continuation.event_id,
        owner_input_event_id=owner_event.event_id,
        missing_names=missing_names,
        previous_locations=previous_locations,
        new_locations=validated_new,
        effective_locations=effective,
        duplicate=False,
    )


def owner_resume_packet(
    store: OrionStateStore,
    *,
    task_id: str,
    owner_input_event_id: str,
) -> dict[str, Any]:
    event = store.get_event(owner_input_event_id)
    if event is None:
        raise OperatorControlDenied(
            "unknown_owner_resume",
            "Owner continuation input does not exist.",
        )
    if event.task_id != task_id or event.event_type != EventType.DECISION:
        raise OperatorControlDenied(
            "invalid_owner_resume",
            "Owner continuation input identity is invalid.",
        )
    payload = dict(event.payload)
    if payload.get("kind") != "owner_continuation_input":
        raise OperatorControlDenied(
            "invalid_owner_resume",
            "DECISION is not owner continuation input.",
        )
    if payload.get("authority") != "owner":
        raise OperatorControlDenied(
            "invalid_owner_resume_authority",
            "Continuation input is not owner-authorized.",
        )
    task = store.get_task(task_id)
    if task is None or task.status != "queued":
        raise OperatorControlDenied(
            "owner_resume_status_mismatch",
            "Owner-resumed task is not queued for the bounded next step.",
        )
    return {
        "schema": "orion.v3.owner-resume-search.v0",
        "task_id": task_id,
        "owner_input_event_id": event.event_id,
        "choice": payload["choice"],
        "missing_names": list(payload["missing_names"]),
        "new_locations": list(payload["new_locations"]),
        "previous_locations": list(payload["previous_locations"]),
        "effective_authorized_locations": list(
            payload["effective_authorized_locations"]
        ),
        "authority": "owner",
    }


def owner_resume_governor_tool_spec() -> dict[str, Any]:
    """Expose one bound continuation control without model-retyped scope.

    The exact missing names and new locations come only from canonical owner
    continuation input already stored by ORION.
    """
    return {
        "type": "function",
        "function": {
            "name": OWNER_RESUME_TOOL_NAME,
            "description": (
                "Continue the exact owner-authorized search amendment already "
                "bound by ORION. This tool has no model-controlled arguments."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    }


def dispatch_bound_owner_resumed_search(
    control: OperatorControlPlane,
    *,
    task_id: str,
    owner_resume: Mapping[str, Any],
    tool_name: str,
    arguments: Mapping[str, Any],
    actor_id: str,
) -> dict[str, Any]:
    """Dispatch the exact owner amendment without model-retyping identity."""
    if tool_name != OWNER_RESUME_TOOL_NAME:
        raise OperatorControlDenied(
            "owner_resume_capability_mismatch",
            "Owner resume requires the bound continuation control.",
        )
    if dict(arguments):
        raise OperatorControlDenied(
            "owner_resume_arguments_forbidden",
            "Bound owner resume accepts no model-controlled arguments.",
        )
    proposal = control.propose_capability_action(
        task_id,
        capability_id="fs.search_exact",
        params={
            "exact_names": list(owner_resume.get("missing_names") or []),
            "locations": list(owner_resume.get("new_locations") or []),
        },
        proposed_by=actor_id,
        parent_event_id=str(owner_resume.get("owner_input_event_id") or ""),
    )
    return {
        "kind": "capability_proposal",
        "status": "PROPOSED",
        "event_id": proposal.event_id,
        "capability_id": proposal.action.capability_id,
        "capability_version": proposal.action.capability_version,
        "action_sha256": proposal.action.action_sha256,
        "approval_class": int(proposal.approval_class),
        "params": dict(proposal.action.params),
    }


def dispatch_owner_resumed_search(
    control: OperatorControlPlane,
    *,
    task_id: str,
    owner_resume: Mapping[str, Any],
    tool_name: str,
    arguments: Mapping[str, Any],
    actor_id: str,
) -> dict[str, Any]:
    """Admit only the exact semantic search authorized by owner resume input."""
    if tool_name != "orion_capability_fs__search_exact":
        raise OperatorControlDenied(
            "owner_resume_capability_mismatch",
            "Owner resume authorizes only fs.search_exact.",
        )
    expected = {
        "exact_names": list(owner_resume.get("missing_names") or []),
        "locations": list(owner_resume.get("new_locations") or []),
    }
    actual = dict(arguments)
    if actual != expected:
        raise OperatorControlDenied(
            "owner_resume_proposal_mismatch",
            "Governor resume proposal does not exactly match owner-authorized missing names and new scope.",
        )
    proposal = control.propose_capability_action(
        task_id,
        capability_id="fs.search_exact",
        params=actual,
        proposed_by=actor_id,
        parent_event_id=str(owner_resume.get("owner_input_event_id") or ""),
    )
    return {
        "kind": "capability_proposal",
        "status": "PROPOSED",
        "event_id": proposal.event_id,
        "capability_id": proposal.action.capability_id,
        "capability_version": proposal.action.capability_version,
        "action_sha256": proposal.action.action_sha256,
        "approval_class": int(proposal.approval_class),
        "params": dict(proposal.action.params),
    }


def decide_resumed_exact_search_progress(
    store: OrionStateStore,
    *,
    task_id: str,
    owner_input_event_id: str,
    result_event_id: str,
) -> ResumedProgressDecision:
    """Combine prior verified evidence with one owner-authorized resume RESULT."""
    task = store.get_task(task_id)
    if task is None:
        raise OperatorControlDenied("unknown_task", "Task does not exist.")

    owner_event = store.get_event(owner_input_event_id)
    if owner_event is None or owner_event.task_id != task_id:
        raise OperatorControlDenied(
            "invalid_owner_resume",
            "Owner continuation input is unavailable for resumed progress.",
        )
    owner_payload = dict(owner_event.payload)
    if (
        owner_event.event_type != EventType.DECISION
        or owner_payload.get("kind") != "owner_continuation_input"
        or owner_payload.get("authority") != "owner"
    ):
        raise OperatorControlDenied(
            "invalid_owner_resume",
            "Resumed progress requires exact owner continuation input.",
        )

    continuation = store.get_event(str(owner_payload.get("continuation_event_id") or ""))
    if continuation is None:
        raise OperatorControlDenied(
            "broken_owner_resume_lineage",
            "Owner continuation parent is missing.",
        )
    progress = store.get_event(str(owner_payload.get("progress_decision_event_id") or ""))
    if progress is None:
        raise OperatorControlDenied(
            "broken_owner_resume_lineage",
            "Original task-progress decision is missing.",
        )
    if continuation.parent_event_id != progress.event_id:
        raise OperatorControlDenied(
            "broken_owner_resume_lineage",
            "Owner resume continuation lineage is broken.",
        )
    progress_payload = dict(progress.payload)
    if (
        progress.event_type != EventType.DECISION
        or progress_payload.get("kind") != "exact_search_task_progress"
        or progress_payload.get("authority") != "orion_deterministic_policy"
    ):
        raise OperatorControlDenied(
            "broken_owner_resume_lineage",
            "Original task-progress decision is invalid.",
        )
    if progress_payload.get("state") != "NEEDS_NEXT_STEP":
        raise OperatorControlDenied(
            "owner_resume_not_needed",
            "Owner resume requires an incomplete prior task-progress decision.",
        )

    packet = verified_result_packet(
        store,
        task_id=task_id,
        result_event_id=result_event_id,
    )
    if packet.get("capability_id") != "fs.search_exact":
        raise OperatorControlDenied(
            "owner_resume_result_mismatch",
            "Owner resume RESULT is not fs.search_exact.",
        )
    if packet.get("searched_locations") != list(owner_payload["new_locations"]):
        raise OperatorControlDenied(
            "owner_resume_result_scope_mismatch",
            "Resumed RESULT does not match the owner-authorized new scope.",
        )

    expected_missing = tuple(str(x) for x in owner_payload["missing_names"])
    result_names = {
        str(item.get("name") or "").casefold()
        for item in packet.get("matches", [])
        if isinstance(item, dict)
    }
    unexpected_names = {
        name for name in result_names
        if name not in {item.casefold() for item in expected_missing}
    }
    if unexpected_names:
        raise OperatorControlDenied(
            "owner_resume_result_name_mismatch",
            "Resumed RESULT contains a basename outside the owner-authorized missing set.",
        )

    required_names = tuple(
        str(x) for x in progress_payload.get("required_exact_names") or []
    )
    prior_found = tuple(
        str(x) for x in progress_payload.get("found_required_names") or []
    )
    found_keys = {name.casefold() for name in prior_found} | result_names
    cumulative_found = tuple(
        name for name in required_names if name.casefold() in found_keys
    )
    remaining = tuple(
        name for name in required_names if name.casefold() not in found_keys
    )
    if remaining:
        state = "NEEDS_NEXT_STEP"
        task_status = "needs_next_step"
        reason = "owner_resumed_search_still_missing_requirements"
    else:
        state = "COMPLETED"
        task_status = "completed"
        reason = "all_required_exact_names_verified_across_owner_authorized_scopes"

    payload = {
        "kind": "exact_search_task_progress",
        "result_event_id": result_event_id,
        "action_sha256": packet["action_sha256"],
        "required_exact_names": list(required_names),
        "required_locations": list(owner_payload["effective_authorized_locations"]),
        "found_required_names": list(cumulative_found),
        "missing_names": list(remaining),
        "verified_match_count": (
            int(progress_payload.get("verified_match_count") or 0)
            + int(packet.get("match_count") or 0)
        ),
        "verified_result_truncated": bool(
            progress_payload.get("verified_result_truncated", False)
            or packet.get("truncated", False)
        ),
        "state": state,
        "reason": reason,
        "authority": "orion_deterministic_policy",
        "resume_from_progress_decision_event_id": progress.event_id,
        "owner_input_event_id": owner_event.event_id,
        "cumulative_result_event_ids": [
            str(progress_payload.get("result_event_id") or ""),
            result_event_id,
        ],
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
                    "resumed_progress_conflict",
                    "A different resumed task-progress decision already exists.",
                )
            conn.commit()
            return ResumedProgressDecision(
                task_id=task_id,
                result_event_id=result_event_id,
                decision_event_id=row["event_id"],
                state=state,
                found_required_names=cumulative_found,
                missing_names=remaining,
                duplicate=True,
            )

        if task.status == "completed":
            raise OperatorControlDenied(
                "task_already_completed",
                "A completed task cannot be resumed.",
            )
        if task.status not in {"queued", "needs_next_step"}:
            raise OperatorControlDenied(
                "owner_resume_status_mismatch",
                "Resumed task is not in an evaluable state.",
            )

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
            UPDATE tasks SET
                status=?,
                updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
            WHERE task_id=?
            """,
            (task_status, task_id),
        )
        if conn.execute("SELECT changes()").fetchone()[0] != 1:
            raise OperatorControlDenied(
                "resumed_progress_update_failed",
                "Resumed task status update did not affect exactly one task.",
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return ResumedProgressDecision(
        task_id=task_id,
        result_event_id=result_event_id,
        decision_event_id=decision.event_id,
        state=state,
        found_required_names=cumulative_found,
        missing_names=remaining,
        duplicate=False,
    )


__all__ = [
    "OWNER_RESUME_TOOL_NAME",
    "OwnerResumeChoice",
    "OwnerScopeResume",
    "ResumedProgressDecision",
    "apply_owner_scope_resume",
    "decide_resumed_exact_search_progress",
    "dispatch_bound_owner_resumed_search",
    "dispatch_owner_resumed_search",
    "owner_resume_governor_tool_spec",
    "owner_resume_packet",
]
