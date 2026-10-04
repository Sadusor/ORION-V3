from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from orion_v3.authority import AuthorityGateway, LeaseAuthority
from orion_v3.evidence import EvidenceEnvelope, Outcome
from orion_v3.state import EventType, OrionStateStore
from orion_v3.workspaces import RegistryDenied, ScopeResolution, WorkspaceRegistry

from .control import OperatorControlDenied


WORKSPACE_SEARCH_CAPABILITY_ID = "workspace.search_exact"
WORKSPACE_SEARCH_CAPABILITY_VERSION = 1


@dataclass(frozen=True)
class WorkspaceSearchProposal:
    event_id: str
    task_id: str
    action_sha256: str
    exact_names: tuple[str, ...]
    scope_token: str
    resolution_id: str
    project_ids: tuple[str, ...]


@dataclass(frozen=True)
class WorkspaceSearchExecution:
    proposal_event_id: str
    action_event_id: str
    evidence_event_id: str
    result_event_id: str
    action_sha256: str
    evidence: EvidenceEnvelope
    verified_result: Mapping[str, Any]


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _safe_names(values: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    output: list[str] = []
    seen: set[str] = set()
    for raw in values:
        name = str(raw or "").strip()
        if not name or "/" in name or "\\" in name or name in {".", ".."}:
            raise OperatorControlDenied(
                "invalid_workspace_search_name",
                "Workspace search requires safe exact basenames.",
            )
        key = name.casefold()
        if key in seen:
            continue
        seen.add(key)
        output.append(name)
    if not output:
        raise OperatorControlDenied(
            "invalid_workspace_search_name",
            "Workspace search requires at least one exact basename.",
        )
    if len(output) > 20:
        raise OperatorControlDenied(
            "workspace_search_name_cap",
            "Workspace search exact-name count exceeds ORION bound.",
        )
    return tuple(output)


def _resolution_material(resolution: ScopeResolution) -> list[dict[str, Any]]:
    return [
        {
            "project_id": project.project_id,
            "name": project.name,
            "repo_identity": project.repo_identity,
            "trust_class": project.trust_class,
            "archive_state": project.archive_state,
            "no_cloud": project.no_cloud,
            "license_state": project.license_state,
            "revision": project.revision,
            "registry_version": project.registry_version,
            "registry_sha256": project.registry_sha256,
        }
        for project in resolution.projects
    ]


def workspace_search_tool_spec(*, allowed_scope_tokens: list[str]) -> dict[str, Any]:
    tokens = sorted({str(item).strip() for item in allowed_scope_tokens if str(item).strip()})
    if not tokens:
        raise ValueError("allowed_scope_tokens must be non-empty")
    return {
        "type": "function",
        "function": {
            "name": "orion_workspace_search_exact",
            "description": (
                "Search exact basenames across one ORION semantic project scope. "
                "ORION resolves the scope to registered projects and trusted roots."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "exact_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "maxItems": 20,
                    },
                    "scope_token": {
                        "type": "string",
                        "enum": tokens,
                    },
                },
                "required": ["exact_names", "scope_token"],
                "additionalProperties": False,
            },
        },
    }


def propose_workspace_search(
    store: OrionStateStore,
    workspace_registry: WorkspaceRegistry,
    *,
    task_id: str,
    exact_names: list[str] | tuple[str, ...],
    scope_token: str,
    proposed_by: str,
    active_project_id: str | None = None,
    max_projects: int = 8,
) -> WorkspaceSearchProposal:
    task = store.get_task(task_id)
    if task is None:
        raise OperatorControlDenied("unknown_task", "Task does not exist.")
    names = _safe_names(exact_names)
    proposed_by = str(proposed_by or "").strip()
    if not proposed_by:
        raise OperatorControlDenied("invalid_actor", "proposed_by must be non-empty")

    try:
        resolution = workspace_registry.resolve_scope(
            scope_token,
            active_project_id=active_project_id,
            max_projects=max_projects,
        )
    except RegistryDenied as exc:
        raise OperatorControlDenied(exc.code, str(exc)) from exc

    action = {
        "capability_id": WORKSPACE_SEARCH_CAPABILITY_ID,
        "capability_version": WORKSPACE_SEARCH_CAPABILITY_VERSION,
        "exact_names": list(names),
        "scope_token": resolution.scope_token,
        "resolution_id": resolution.resolution_id,
        "projects": _resolution_material(resolution),
        "execution_policy": {
            "recursive": True,
            "max_depth": 4,
            "max_results": 50,
        },
    }
    action_sha = _sha256(action)
    event = store.append_event(
        task.project_id,
        EventType.PROPOSAL,
        {
            "kind": "workspace_search_proposed",
            "action_sha256": action_sha,
            "action": action,
        },
        actor_kind="local_operator",
        actor_id=proposed_by,
        task_id=task_id,
    )
    return WorkspaceSearchProposal(
        event_id=event.event_id,
        task_id=task_id,
        action_sha256=action_sha,
        exact_names=names,
        scope_token=resolution.scope_token,
        resolution_id=resolution.resolution_id,
        project_ids=tuple(project.project_id for project in resolution.projects),
    )


def _reload_proposal(
    store: OrionStateStore,
    *,
    task_id: str,
    proposal_event_id: str,
) -> tuple[Any, dict[str, Any], str]:
    event = store.get_event(proposal_event_id)
    if event is None:
        raise OperatorControlDenied("unknown_proposal", "Workspace search proposal does not exist.")
    if event.task_id != task_id:
        raise OperatorControlDenied("wrong_task", "Workspace search proposal belongs to another task.")
    if event.event_type != EventType.PROPOSAL:
        raise OperatorControlDenied("invalid_proposal_event", "Workspace search requires PROPOSAL.")
    payload = dict(event.payload)
    if payload.get("kind") != "workspace_search_proposed":
        raise OperatorControlDenied("invalid_proposal_event", "Proposal is not workspace search.")
    action = payload.get("action")
    if not isinstance(action, Mapping):
        raise OperatorControlDenied("invalid_proposal_event", "Workspace proposal lacks action.")
    action = dict(action)
    if action.get("capability_id") != WORKSPACE_SEARCH_CAPABILITY_ID:
        raise OperatorControlDenied("invalid_proposal_event", "Workspace capability identity changed.")
    if action.get("capability_version") != WORKSPACE_SEARCH_CAPABILITY_VERSION:
        raise OperatorControlDenied("stale_capability_version", "Workspace capability version changed.")
    names = _safe_names(list(action.get("exact_names") or []))
    if list(names) != list(action.get("exact_names") or []):
        raise OperatorControlDenied("proposal_normalization_mismatch", "Workspace names are not canonical.")
    projects = action.get("projects")
    if not isinstance(projects, list) or not projects:
        raise OperatorControlDenied("invalid_proposal_event", "Workspace proposal has no frozen projects.")
    policy = action.get("execution_policy")
    if policy != {"recursive": True, "max_depth": 4, "max_results": 50}:
        raise OperatorControlDenied(
            "proposal_policy_tamper",
            "Workspace search execution policy is not canonical.",
        )
    action_sha = _sha256(action)
    if payload.get("action_sha256") != action_sha:
        raise OperatorControlDenied("proposal_tamper_detected", "Workspace proposal hash mismatch.")
    return event, action, action_sha


def _validate_frozen_resolution(
    workspace_registry: WorkspaceRegistry,
    action: Mapping[str, Any],
) -> tuple[list[str], dict[str, str], dict[str, dict[str, Any]]]:
    project_ids: list[str] = []
    roots: dict[str, str] = {}
    provenance: dict[str, dict[str, Any]] = {}
    for frozen in action["projects"]:
        if not isinstance(frozen, Mapping):
            raise OperatorControlDenied("invalid_proposal_event", "Frozen project is not structured.")
        project_id = str(frozen.get("project_id") or "")
        try:
            current = workspace_registry.get_project(project_id)
        except RegistryDenied as exc:
            raise OperatorControlDenied(exc.code, str(exc)) from exc
        if (
            current.version != int(frozen.get("registry_version"))
            or current.record_sha256 != str(frozen.get("registry_sha256") or "")
            or current.revision != frozen.get("revision")
            or current.name != frozen.get("name")
            or current.repo_identity != frozen.get("repo_identity")
            or current.trust_class.value != frozen.get("trust_class")
            or current.archive_state.value != frozen.get("archive_state")
            or current.no_cloud != bool(frozen.get("no_cloud"))
            or current.license_state != frozen.get("license_state")
        ):
            raise OperatorControlDenied(
                "workspace_scope_stale",
                "Registered project changed after workspace scope was frozen.",
            )
        project_ids.append(project_id)
        roots[project_id] = current.trusted_root
        provenance[project_id] = {
            "project_id": current.project_id,
            "project_name": current.name,
            "repo_identity": current.repo_identity,
            "revision": current.revision,
            "trust_class": current.trust_class.value,
            "archive_state": current.archive_state.value,
            "no_cloud": current.no_cloud,
            "license_state": current.license_state,
            "registry_version": current.version,
            "registry_sha256": current.record_sha256,
        }
    resolution_material = {
        "scope_token": action["scope_token"],
        "projects": [
            {
                "project_id": item["project_id"],
                "registry_version": item["registry_version"],
                "registry_sha256": item["registry_sha256"],
            }
            for item in action["projects"]
        ],
    }
    if _sha256(resolution_material) != action["resolution_id"]:
        raise OperatorControlDenied(
            "workspace_resolution_tamper",
            "Frozen workspace scope resolution ID is invalid.",
        )
    return project_ids, roots, provenance


def _run_openjarvis_search(
    *,
    task_id: str,
    exact_names: list[str],
    project_ids: list[str],
    trusted_roots: Mapping[str, str | Path],
) -> tuple[EvidenceEnvelope, str]:
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
            "locations": project_ids,
            "recursive": True,
            "max_depth": 4,
            "max_results": 50,
            "workspace_resolution_bound": True,
        },
        ttl_seconds=60,
    )
    agent_id = "orion-workspace-read-dispatch"
    policy = build_gate1_capability_policy(agent_id)
    tool = build_registered_filesystem_search_tool(
        gateway,
        lease_token=issued.token,
        trusted_roots=trusted_roots,
    )
    executor = ToolExecutor([tool], capability_policy=policy, agent_id=agent_id)
    arguments = {
        "exact_names": exact_names,
        "locations": project_ids,
        "recursive": True,
        "max_depth": 4,
        "max_results": 50,
    }
    result = executor.execute(
        ToolCall(
            id="orion-workspace-filesystem-search",
            name=tool.tool_id,
            arguments=json.dumps(arguments, ensure_ascii=False),
        )
    )
    evidence = normalize_filesystem_search_evidence(lease=issued.lease, tool_result=result)
    return evidence, issued.lease.lease_id


def execute_workspace_search(
    store: OrionStateStore,
    workspace_registry: WorkspaceRegistry,
    *,
    task_id: str,
    proposal_event_id: str,
) -> WorkspaceSearchExecution:
    proposal, action, action_sha = _reload_proposal(
        store,
        task_id=task_id,
        proposal_event_id=proposal_event_id,
    )
    existing = store.connect().execute(
        """
        SELECT event_id FROM events
        WHERE parent_event_id=? AND event_type=?
        ORDER BY rowid ASC LIMIT 1
        """,
        (proposal.event_id, EventType.ACTION.value),
    ).fetchone()
    if existing is not None:
        raise OperatorControlDenied(
            "proposal_already_dispatched",
            "Workspace search proposal has already entered execution.",
        )

    project_ids, trusted_roots, provenance = _validate_frozen_resolution(
        workspace_registry,
        action,
    )

    action_event = store.append_event(
        proposal.project_id,
        EventType.ACTION,
        {
            "kind": "workspace_search_dispatch",
            "proposal_event_id": proposal.event_id,
            "action_sha256": action_sha,
            "capability_id": WORKSPACE_SEARCH_CAPABILITY_ID,
            "capability_version": WORKSPACE_SEARCH_CAPABILITY_VERSION,
            "scope_token": action["scope_token"],
            "resolution_id": action["resolution_id"],
            "project_ids": project_ids,
            "operation_id": "filesystem.search",
            "implementation_id": "openjarvis.tool.orion_filesystem_search.v1",
        },
        actor_kind="orion",
        actor_id="workspace-read-dispatch",
        task_id=task_id,
        parent_event_id=proposal.event_id,
    )

    evidence, lease_id = _run_openjarvis_search(
        task_id=task_id,
        exact_names=list(action["exact_names"]),
        project_ids=project_ids,
        trusted_roots=trusted_roots,
    )
    evidence_event = store.append_event(
        proposal.project_id,
        EventType.EVIDENCE,
        {
            "kind": "workspace_search_evidence",
            "proposal_event_id": proposal.event_id,
            "action_event_id": action_event.event_id,
            "action_sha256": action_sha,
            "lease_id": lease_id,
            "scope_token": action["scope_token"],
            "resolution_id": action["resolution_id"],
            "outcome": evidence.outcome.value,
            "operation_id": evidence.operation_id,
            "implementation_id": evidence.implementation_id,
            "result": dict(evidence.result),
            "verifier": evidence.verifier,
            "error": evidence.error,
        },
        actor_kind="orion",
        actor_id="workspace-evidence-normalizer",
        task_id=task_id,
        parent_event_id=action_event.event_id,
    )

    if evidence.outcome != Outcome.CONFIRMED:
        raise OperatorControlDenied(
            "hand_evidence_not_confirmed",
            "Workspace filesystem search did not produce confirmed evidence.",
        )
    result = dict(evidence.result)
    if result.get("searched_locations") != project_ids:
        raise OperatorControlDenied(
            "workspace_evidence_scope_mismatch",
            "Workspace evidence searched a different frozen project set.",
        )
    matches = result.get("matches")
    if not isinstance(matches, list) or result.get("match_count") != len(matches):
        raise OperatorControlDenied(
            "workspace_evidence_invalid",
            "Workspace search evidence is structurally invalid.",
        )
    wanted = {name.casefold() for name in action["exact_names"]}
    verified_matches: list[dict[str, Any]] = []
    for raw in matches:
        if not isinstance(raw, Mapping):
            raise OperatorControlDenied("workspace_evidence_invalid", "Match is not structured.")
        item = dict(raw)
        project_id = str(item.get("location") or "")
        relative_path = str(item.get("relative_path") or "")
        name = str(item.get("name") or "")
        relative = PurePosixPath(relative_path)
        if project_id not in provenance:
            raise OperatorControlDenied(
                "workspace_evidence_scope_mismatch",
                "Workspace evidence escaped the frozen project set.",
            )
        if (
            not relative_path
            or relative.is_absolute()
            or ":" in relative_path
            or any(part in {"", ".", ".."} for part in relative.parts)
        ):
            raise OperatorControlDenied(
                "workspace_evidence_path_invalid",
                "Workspace evidence contains unsafe relative path.",
            )
        if name.casefold() not in wanted:
            raise OperatorControlDenied(
                "workspace_evidence_name_mismatch",
                "Workspace evidence contains unrequested basename.",
            )
        verified_matches.append(
            {
                **provenance[project_id],
                "relative_path": relative_path,
                "name": name,
                "kind": str(item.get("kind") or ""),
                "path_identity_sha256": _sha256(
                    {
                        "project_id": project_id,
                        "revision": provenance[project_id]["revision"],
                        "relative_path": relative_path,
                    }
                ),
            }
        )

    verified = {
        "status": "PASS",
        "capability_id": WORKSPACE_SEARCH_CAPABILITY_ID,
        "scope_token": action["scope_token"],
        "resolution_id": action["resolution_id"],
        "project_ids": project_ids,
        "searched_project_count": len(project_ids),
        "match_count": len(verified_matches),
        "found_names": sorted({item["name"] for item in verified_matches}),
        "matches": verified_matches,
        "truncated": bool(result.get("truncated", False)),
        "absolute_roots_exposed": False,
    }
    result_event = store.append_event(
        proposal.project_id,
        EventType.RESULT,
        {
            "kind": "workspace_search_result",
            "proposal_event_id": proposal.event_id,
            "action_event_id": action_event.event_id,
            "evidence_event_id": evidence_event.event_id,
            "action_sha256": action_sha,
            "verification": verified,
        },
        actor_kind="orion",
        actor_id="workspace-deterministic-verifier",
        task_id=task_id,
        parent_event_id=evidence_event.event_id,
    )
    return WorkspaceSearchExecution(
        proposal_event_id=proposal.event_id,
        action_event_id=action_event.event_id,
        evidence_event_id=evidence_event.event_id,
        result_event_id=result_event.event_id,
        action_sha256=action_sha,
        evidence=evidence,
        verified_result=verified,
    )


__all__ = [
    "WORKSPACE_SEARCH_CAPABILITY_ID",
    "WORKSPACE_SEARCH_CAPABILITY_VERSION",
    "WorkspaceSearchExecution",
    "WorkspaceSearchProposal",
    "execute_workspace_search",
    "propose_workspace_search",
    "workspace_search_tool_spec",
]
