from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping

from orion_v3.authority import AuthorityGateway, LeaseAuthority
from orion_v3.capabilities import ApprovalClass, CapabilityRegistry, inherited_registry_v0
from orion_v3.evidence import EvidenceEnvelope, Outcome
from orion_v3.state import EventRecord, EventType, OrionStateStore

from .control import OperatorControlDenied


@dataclass(frozen=True)
class RoutineExecutionResult:
    proposal_event_id: str
    action_event_id: str
    evidence_event_id: str
    result_event_id: str
    capability_id: str
    action_sha256: str
    evidence: EvidenceEnvelope
    verified_result: Mapping[str, Any]


SearchRunner = Callable[
    [str, Mapping[str, Any], Mapping[str, str | Path]],
    tuple[EvidenceEnvelope, str],
]


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _require_proposal(
    store: OrionStateStore,
    registry: CapabilityRegistry,
    *,
    task_id: str,
    proposal_event_id: str,
) -> tuple[EventRecord, dict[str, Any], str]:
    event = store.get_event(proposal_event_id)
    if event is None:
        raise OperatorControlDenied(
            "unknown_proposal",
            "Capability proposal event does not exist.",
        )
    if event.task_id != task_id:
        raise OperatorControlDenied(
            "wrong_task",
            "Capability proposal belongs to a different task.",
        )
    if event.event_type != EventType.PROPOSAL:
        raise OperatorControlDenied(
            "invalid_proposal_event",
            "Routine execution requires a PROPOSAL event.",
        )

    payload = dict(event.payload)
    if payload.get("kind") != "capability_action_proposed":
        raise OperatorControlDenied(
            "invalid_proposal_event",
            "Event is not a semantic capability-action proposal.",
        )
    action = payload.get("action")
    if not isinstance(action, Mapping):
        raise OperatorControlDenied(
            "invalid_proposal_event",
            "Proposal lacks a structured frozen action.",
        )

    capability_id = str(action.get("capability_id") or "")
    definition = registry.get(capability_id)
    try:
        version = int(action.get("capability_version"))
    except (TypeError, ValueError) as exc:
        raise OperatorControlDenied(
            "invalid_proposal_event",
            "Proposal capability version is invalid.",
        ) from exc
    if version != definition.version:
        raise OperatorControlDenied(
            "stale_capability_version",
            "Proposal capability version no longer matches the registry.",
        )

    params = action.get("params")
    if not isinstance(params, Mapping):
        raise OperatorControlDenied(
            "invalid_proposal_event",
            "Proposal parameters are not an object.",
        )
    normalized = definition.normalize_params(params)
    if dict(params) != normalized:
        raise OperatorControlDenied(
            "proposal_normalization_mismatch",
            "Stored proposal parameters are not canonical.",
        )

    frozen = {
        "capability_id": definition.capability_id,
        "capability_version": definition.version,
        "params": normalized,
    }
    action_sha = _sha256(frozen)
    if payload.get("action_sha256") != action_sha:
        raise OperatorControlDenied(
            "proposal_tamper_detected",
            "Capability proposal failed its canonical content hash.",
        )

    if definition.approval_class != ApprovalClass.READ_ONLY:
        raise OperatorControlDenied(
            "routine_auto_dispatch_forbidden",
            "Only READ_ONLY capability proposals may use routine auto-dispatch.",
        )

    return event, frozen, action_sha


def _default_search_runner(
    task_id: str,
    params: Mapping[str, Any],
    trusted_roots: Mapping[str, str | Path],
) -> tuple[EvidenceEnvelope, str]:
    # Donor imports are lazy so core/unit tests do not require OpenJarvis.
    from openjarvis.core.types import ToolCall
    from openjarvis.tools._stubs import ToolExecutor
    from orion_v3.substrates.openjarvis import (
        build_gate1_capability_policy,
        build_registered_filesystem_search_tool,
        normalize_filesystem_search_evidence,
    )

    leases = LeaseAuthority()
    gateway = AuthorityGateway(leases)
    issued = leases.issue(
        task_id=task_id,
        operation_id="filesystem.search",
        principal="orion",
        scope={
            "locations": list(params["locations"]),
            "recursive": bool(params["recursive"]),
            "max_depth": int(params["max_depth"]),
            "max_results": int(params["max_results"]),
        },
        ttl_seconds=60,
    )

    agent_id = "orion-production-routine-dispatch"
    policy = build_gate1_capability_policy(agent_id)
    tool = build_registered_filesystem_search_tool(
        gateway,
        lease_token=issued.token,
        trusted_roots=trusted_roots,
    )
    executor = ToolExecutor(
        [tool],
        capability_policy=policy,
        agent_id=agent_id,
    )
    arguments = {
        "exact_names": list(params["exact_names"]),
        "locations": list(params["locations"]),
        "recursive": bool(params["recursive"]),
        "max_depth": int(params["max_depth"]),
        "max_results": int(params["max_results"]),
    }
    result = executor.execute(
        ToolCall(
            id="orion-production-filesystem-search",
            name=tool.tool_id,
            arguments=json.dumps(arguments, ensure_ascii=False),
        )
    )
    evidence = normalize_filesystem_search_evidence(
        lease=issued.lease,
        tool_result=result,
    )
    return evidence, issued.lease.lease_id


def _verify_filesystem_search(
    evidence: EvidenceEnvelope,
    *,
    params: Mapping[str, Any],
) -> dict[str, Any]:
    if evidence.outcome != Outcome.CONFIRMED:
        raise OperatorControlDenied(
            "hand_evidence_not_confirmed",
            "Filesystem search did not produce confirmed evidence.",
        )
    if evidence.operation_id != "filesystem.search":
        raise OperatorControlDenied(
            "hand_evidence_operation_mismatch",
            "Filesystem search evidence operation identity changed.",
        )
    if evidence.implementation_id != "openjarvis.tool.orion_filesystem_search.v1":
        raise OperatorControlDenied(
            "hand_evidence_implementation_mismatch",
            "Filesystem search evidence implementation identity changed.",
        )

    result = dict(evidence.result)
    searched = result.get("searched_locations")
    if searched != list(params["locations"]):
        raise OperatorControlDenied(
            "hand_evidence_scope_mismatch",
            "Filesystem search evidence does not match proposed locations.",
        )
    matches = result.get("matches")
    if not isinstance(matches, list):
        raise OperatorControlDenied(
            "hand_evidence_invalid",
            "Filesystem search evidence matches are not an array.",
        )
    if result.get("match_count") != len(matches):
        raise OperatorControlDenied(
            "hand_evidence_invalid",
            "Filesystem search evidence match_count is inconsistent.",
        )

    allowed_locations = set(params["locations"])
    requested_names = {str(name).casefold() for name in params["exact_names"]}
    verified_matches: list[dict[str, Any]] = []
    for raw in matches:
        if not isinstance(raw, Mapping):
            raise OperatorControlDenied(
                "hand_evidence_invalid",
                "Filesystem search match is not structured.",
            )
        item = dict(raw)
        location = str(item.get("location") or "")
        relative_path = str(item.get("relative_path") or "")
        name = str(item.get("name") or "")
        relative = PurePosixPath(relative_path)
        if location not in allowed_locations:
            raise OperatorControlDenied(
                "hand_evidence_scope_mismatch",
                "Filesystem search evidence escaped the proposed location.",
            )
        if (
            not relative_path
            or relative.is_absolute()
            or ":" in relative_path
            or any(part in {"", ".", ".."} for part in relative.parts)
        ):
            raise OperatorControlDenied(
                "hand_evidence_path_invalid",
                "Filesystem search evidence contains an unsafe relative path.",
            )
        if name.casefold() not in requested_names:
            raise OperatorControlDenied(
                "hand_evidence_name_mismatch",
                "Filesystem search returned a basename that was not requested.",
            )
        verified_matches.append(item)

    found_names = sorted({str(item["name"]) for item in verified_matches})
    return {
        "status": "PASS",
        "operation_id": evidence.operation_id,
        "implementation_id": evidence.implementation_id,
        "searched_locations": list(searched),
        "match_count": len(verified_matches),
        "found_names": found_names,
        "matches": verified_matches,
        "truncated": bool(result.get("truncated", False)),
    }


def execute_read_only_proposal(
    store: OrionStateStore,
    *,
    task_id: str,
    proposal_event_id: str,
    trusted_roots: Mapping[str, str | Path],
    registry: CapabilityRegistry | None = None,
    search_runner: SearchRunner | None = None,
) -> RoutineExecutionResult:
    """Execute one canonical READ_ONLY semantic proposal under ORION authority.

    The proposal is reloaded from the append-only ledger and revalidated before
    any lease is issued. The model never supplies a lease or trusted root.
    """
    registry = registry or inherited_registry_v0()
    proposal, frozen, action_sha = _require_proposal(
        store,
        registry,
        task_id=task_id,
        proposal_event_id=proposal_event_id,
    )
    capability_id = str(frozen["capability_id"])
    params = dict(frozen["params"])

    if capability_id != "fs.search_exact":
        raise OperatorControlDenied(
            "routine_capability_not_implemented",
            "No production routine executor is registered for this capability.",
        )

    existing_dispatch = store.connect().execute(
        """
        SELECT event_id FROM events
        WHERE parent_event_id=? AND event_type=?
        ORDER BY rowid ASC
        LIMIT 1
        """,
        (proposal.event_id, EventType.ACTION.value),
    ).fetchone()
    if existing_dispatch is not None:
        raise OperatorControlDenied(
            "proposal_already_dispatched",
            "This semantic proposal has already entered execution.",
        )

    action_event = store.append_event(
        proposal.project_id,
        EventType.ACTION,
        {
            "kind": "routine_capability_dispatch",
            "proposal_event_id": proposal.event_id,
            "action_sha256": action_sha,
            "capability_id": capability_id,
            "capability_version": frozen["capability_version"],
            "operation_id": "filesystem.search",
            "implementation_id": "openjarvis.tool.orion_filesystem_search.v1",
        },
        actor_kind="orion",
        actor_id="routine-dispatch",
        task_id=task_id,
        parent_event_id=proposal.event_id,
    )

    runner = search_runner or _default_search_runner
    evidence, lease_id = runner(task_id, params, trusted_roots)
    evidence_payload = {
        "kind": "hand_evidence",
        "proposal_event_id": proposal.event_id,
        "action_event_id": action_event.event_id,
        "action_sha256": action_sha,
        "lease_id": lease_id,
        "operation_id": evidence.operation_id,
        "implementation_id": evidence.implementation_id,
        "outcome": evidence.outcome.value,
        "result": dict(evidence.result),
        "verifier": evidence.verifier,
        "error": evidence.error,
    }
    evidence_event = store.append_event(
        proposal.project_id,
        EventType.EVIDENCE,
        evidence_payload,
        actor_kind="orion",
        actor_id="evidence-normalizer",
        task_id=task_id,
        parent_event_id=action_event.event_id,
    )

    verified = _verify_filesystem_search(evidence, params=params)
    result_event = store.append_event(
        proposal.project_id,
        EventType.RESULT,
        {
            "kind": "routine_capability_result",
            "proposal_event_id": proposal.event_id,
            "action_event_id": action_event.event_id,
            "evidence_event_id": evidence_event.event_id,
            "action_sha256": action_sha,
            "capability_id": capability_id,
            "verification": verified,
        },
        actor_kind="orion",
        actor_id="deterministic-verifier",
        task_id=task_id,
        parent_event_id=evidence_event.event_id,
    )

    return RoutineExecutionResult(
        proposal_event_id=proposal.event_id,
        action_event_id=action_event.event_id,
        evidence_event_id=evidence_event.event_id,
        result_event_id=result_event.event_id,
        capability_id=capability_id,
        action_sha256=action_sha,
        evidence=evidence,
        verified_result=verified,
    )
