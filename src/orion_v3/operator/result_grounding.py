from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any

from orion_v3.state import EventType, OrionStateStore

from .control import OperatorControlDenied


def verified_result_packet(
    store: OrionStateStore,
    *,
    task_id: str,
    result_event_id: str,
) -> dict[str, Any]:
    """Build a model-safe packet from one deterministically verified RESULT.

    The packet exposes only verified semantic result data. It never exposes
    trusted roots, Action-Lease tokens, raw Hand prose, or donor internals.
    """
    result_event = store.get_event(result_event_id)
    if result_event is None:
        raise OperatorControlDenied(
            "unknown_result",
            "Verified RESULT event does not exist.",
        )
    if result_event.task_id != task_id:
        raise OperatorControlDenied(
            "wrong_task",
            "RESULT belongs to a different task.",
        )
    if result_event.event_type != EventType.RESULT:
        raise OperatorControlDenied(
            "invalid_result_event",
            "Governor result grounding requires a RESULT event.",
        )

    result_payload = dict(result_event.payload)
    if result_payload.get("kind") != "routine_capability_result":
        raise OperatorControlDenied(
            "invalid_result_event",
            "RESULT is not a routine capability result.",
        )

    verification = result_payload.get("verification")
    if not isinstance(verification, dict) or verification.get("status") != "PASS":
        raise OperatorControlDenied(
            "unverified_result",
            "RESULT does not carry deterministic PASS verification.",
        )

    evidence_event_id = str(result_payload.get("evidence_event_id") or "")
    action_event_id = str(result_payload.get("action_event_id") or "")
    proposal_event_id = str(result_payload.get("proposal_event_id") or "")
    action_sha = str(result_payload.get("action_sha256") or "")
    capability_id = str(result_payload.get("capability_id") or "")
    if not all(
        [
            evidence_event_id,
            action_event_id,
            proposal_event_id,
            action_sha,
            capability_id,
        ]
    ):
        raise OperatorControlDenied(
            "invalid_result_event",
            "RESULT is missing causal identity fields.",
        )

    evidence_event = store.get_event(evidence_event_id)
    action_event = store.get_event(action_event_id)
    proposal_event = store.get_event(proposal_event_id)
    if evidence_event is None or action_event is None or proposal_event is None:
        raise OperatorControlDenied(
            "broken_result_lineage",
            "RESULT causal lineage is incomplete.",
        )
    lineage = [proposal_event, action_event, evidence_event, result_event]
    if any(event.task_id != task_id for event in lineage):
        raise OperatorControlDenied(
            "broken_result_lineage",
            "RESULT lineage crosses task boundaries.",
        )
    if proposal_event.event_type != EventType.PROPOSAL:
        raise OperatorControlDenied(
            "broken_result_lineage",
            "RESULT lineage does not begin with PROPOSAL.",
        )
    if action_event.event_type != EventType.ACTION:
        raise OperatorControlDenied(
            "broken_result_lineage",
            "RESULT lineage lacks ACTION.",
        )
    if evidence_event.event_type != EventType.EVIDENCE:
        raise OperatorControlDenied(
            "broken_result_lineage",
            "RESULT lineage lacks EVIDENCE.",
        )
    if action_event.parent_event_id != proposal_event.event_id:
        raise OperatorControlDenied(
            "broken_result_lineage",
            "ACTION is not parented to the proposal.",
        )
    if evidence_event.parent_event_id != action_event.event_id:
        raise OperatorControlDenied(
            "broken_result_lineage",
            "EVIDENCE is not parented to the action.",
        )
    if result_event.parent_event_id != evidence_event.event_id:
        raise OperatorControlDenied(
            "broken_result_lineage",
            "RESULT is not parented to the evidence.",
        )

    proposal_payload = dict(proposal_event.payload)
    action_payload = dict(action_event.payload)
    evidence_payload = dict(evidence_event.payload)
    if proposal_payload.get("action_sha256") != action_sha:
        raise OperatorControlDenied(
            "result_identity_mismatch",
            "RESULT action hash differs from proposal.",
        )
    if action_payload.get("action_sha256") != action_sha:
        raise OperatorControlDenied(
            "result_identity_mismatch",
            "RESULT action hash differs from ACTION.",
        )
    if evidence_payload.get("action_sha256") != action_sha:
        raise OperatorControlDenied(
            "result_identity_mismatch",
            "RESULT action hash differs from EVIDENCE.",
        )
    if action_payload.get("proposal_event_id") != proposal_event_id:
        raise OperatorControlDenied(
            "result_identity_mismatch",
            "ACTION proposal identity mismatch.",
        )
    if evidence_payload.get("proposal_event_id") != proposal_event_id:
        raise OperatorControlDenied(
            "result_identity_mismatch",
            "EVIDENCE proposal identity mismatch.",
        )
    if evidence_payload.get("action_event_id") != action_event_id:
        raise OperatorControlDenied(
            "result_identity_mismatch",
            "EVIDENCE action identity mismatch.",
        )

    matches = verification.get("matches")
    if not isinstance(matches, list):
        raise OperatorControlDenied(
            "invalid_verified_result",
            "Verified RESULT matches are not an array.",
        )

    safe_matches: list[dict[str, Any]] = []
    for raw in matches:
        if not isinstance(raw, dict):
            raise OperatorControlDenied(
                "invalid_verified_result",
                "Verified RESULT contains an unstructured match.",
            )
        relative_path = str(raw.get("relative_path") or "")
        relative = PurePosixPath(relative_path)
        if (
            not relative_path
            or relative.is_absolute()
            or ":" in relative_path
            or any(part in {"", ".", ".."} for part in relative.parts)
        ):
            raise OperatorControlDenied(
                "invalid_verified_result",
                "Verified RESULT contains an unsafe relative path.",
            )
        safe_matches.append(
            {
                "location": str(raw.get("location") or ""),
                "relative_path": relative_path,
                "name": str(raw.get("name") or ""),
                "kind": str(raw.get("kind") or ""),
            }
        )

    found_names = verification.get("found_names")
    if not isinstance(found_names, list):
        raise OperatorControlDenied(
            "invalid_verified_result",
            "Verified RESULT found_names are not an array.",
        )

    return {
        "schema": "orion.v3.verified-result-packet.v0",
        "task_id": task_id,
        "result_event_id": result_event.event_id,
        "capability_id": capability_id,
        "action_sha256": action_sha,
        "verification_status": "PASS",
        "operation_id": str(verification.get("operation_id") or ""),
        "implementation_id": str(verification.get("implementation_id") or ""),
        "searched_locations": list(verification.get("searched_locations") or []),
        "match_count": int(verification.get("match_count") or 0),
        "found_names": [str(name) for name in found_names],
        "matches": safe_matches,
        "truncated": bool(verification.get("truncated", False)),
        "authority": "verified_evidence_only",
    }
