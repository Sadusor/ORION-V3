from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from orion_v3.state import EventType, OrionStateStore
from orion_v3.workspaces import RegistryDenied, WorkspaceRegistry

from .control import OperatorControlDenied


VERIFIED_TEXT_READ_CAPABILITY_ID = "workspace.read_verified_text"
VERIFIED_TEXT_READ_VERSION = 1


@dataclass(frozen=True)
class VerifiedTextReadResult:
    action_event_id: str
    evidence_event_id: str
    result_event_id: str
    project_id: str
    relative_path: str
    path_identity_sha256: str
    content_sha256: str
    text: str
    bytes_read: int
    truncated: bool


def verified_text_read_tool_spec() -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "orion_read_verified_text",
            "description": (
                "Read bounded UTF-8 text from an exact previously verified "
                "workspace-search evidence item. The model supplies only the "
                "evidence identity, never a filesystem path."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path_identity_sha256": {
                        "type": "string",
                        "minLength": 64,
                        "maxLength": 64,
                    },
                },
                "required": ["path_identity_sha256"],
                "additionalProperties": False,
            },
        },
    }


def _find_workspace_match(
    store: OrionStateStore,
    *,
    task_id: str,
    workspace_result_event_id: str,
    path_identity_sha256: str,
) -> tuple[Any, dict[str, Any]]:
    event = store.get_event(workspace_result_event_id)
    if event is None:
        raise OperatorControlDenied(
            "unknown_workspace_result",
            "Workspace RESULT event does not exist.",
        )
    if event.task_id != task_id:
        raise OperatorControlDenied(
            "wrong_task",
            "Workspace RESULT belongs to another task.",
        )
    if event.event_type != EventType.RESULT:
        raise OperatorControlDenied(
            "invalid_workspace_result",
            "Verified text read requires a RESULT event.",
        )
    payload = dict(event.payload)
    if payload.get("kind") != "workspace_search_result":
        raise OperatorControlDenied(
            "invalid_workspace_result",
            "RESULT is not workspace-search evidence.",
        )
    verification = payload.get("verification")
    if not isinstance(verification, Mapping):
        raise OperatorControlDenied(
            "invalid_workspace_result",
            "Workspace RESULT lacks verification.",
        )
    verification = dict(verification)
    if verification.get("status") != "PASS":
        raise OperatorControlDenied(
            "workspace_result_not_verified",
            "Workspace RESULT is not deterministically verified.",
        )
    matches = verification.get("matches")
    if not isinstance(matches, list):
        raise OperatorControlDenied(
            "invalid_workspace_result",
            "Workspace RESULT matches are invalid.",
        )
    identity = str(path_identity_sha256 or "").strip().lower()
    if len(identity) != 64 or any(ch not in "0123456789abcdef" for ch in identity):
        raise OperatorControlDenied(
            "invalid_evidence_identity",
            "path_identity_sha256 must be a lowercase SHA256 hex digest.",
        )
    found = [
        dict(item)
        for item in matches
        if isinstance(item, Mapping)
        and str(item.get("path_identity_sha256") or "").lower() == identity
    ]
    if len(found) != 1:
        raise OperatorControlDenied(
            "unknown_evidence_identity",
            "Evidence identity must resolve to exactly one verified match.",
        )
    return event, found[0]


def read_verified_workspace_text(
    store: OrionStateStore,
    workspace_registry: WorkspaceRegistry,
    *,
    task_id: str,
    workspace_result_event_id: str,
    path_identity_sha256: str,
    max_bytes: int = 32768,
) -> VerifiedTextReadResult:
    """Read bounded text from exact verified workspace-search evidence.

    No model-supplied path is accepted. The registry entry must still match the
    frozen provenance carried by the verified search result.
    """
    if max_bytes < 1 or max_bytes > 262144:
        raise OperatorControlDenied(
            "invalid_read_bound",
            "max_bytes must be between 1 and 262144.",
        )

    result_event, match = _find_workspace_match(
        store,
        task_id=task_id,
        workspace_result_event_id=workspace_result_event_id,
        path_identity_sha256=path_identity_sha256,
    )

    project_id = str(match.get("project_id") or "")
    relative_path = str(match.get("relative_path") or "")
    if not project_id or not relative_path:
        raise OperatorControlDenied(
            "invalid_workspace_result",
            "Verified match lacks project/path identity.",
        )

    try:
        current = workspace_registry.get_project(project_id)
    except RegistryDenied as exc:
        raise OperatorControlDenied(exc.code, str(exc)) from exc

    if (
        current.version != int(match.get("registry_version"))
        or current.record_sha256 != str(match.get("registry_sha256") or "")
        or current.revision != match.get("revision")
        or current.repo_identity != match.get("repo_identity")
        or current.name != match.get("project_name")
        or current.trust_class.value != match.get("trust_class")
        or current.no_cloud != bool(match.get("no_cloud"))
        or current.license_state != match.get("license_state")
    ):
        raise OperatorControlDenied(
            "workspace_evidence_stale",
            "Registered project changed after verified search evidence was produced.",
        )

    root = Path(current.trusted_root).resolve()
    candidate = root.joinpath(*relative_path.split("/"))
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise OperatorControlDenied(
            "verified_file_unavailable",
            "Verified file is no longer available.",
        ) from exc

    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise OperatorControlDenied(
            "verified_path_escape",
            "Verified relative path escaped its trusted project root.",
        ) from exc

    if candidate.is_symlink() or str(match.get("kind") or "") != "file":
        raise OperatorControlDenied(
            "verified_file_not_regular",
            "Verified evidence must refer to a non-symlink regular file.",
        )
    if not resolved.is_file():
        raise OperatorControlDenied(
            "verified_file_unavailable",
            "Verified path is not a regular file.",
        )

    stat = resolved.stat()
    expected_size = match.get("size_bytes")
    expected_modified_ns = match.get("modified_ns")
    if (
        expected_size is None
        or expected_modified_ns is None
        or int(expected_size) != stat.st_size
        or int(expected_modified_ns) != stat.st_mtime_ns
    ):
        raise OperatorControlDenied(
            "workspace_file_changed",
            "Verified file metadata changed after workspace search evidence.",
        )

    with resolved.open("rb") as handle:
        raw = handle.read(max_bytes + 1)
    truncated = len(raw) > max_bytes
    bounded = raw[:max_bytes]
    try:
        text = bounded.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise OperatorControlDenied(
            "verified_file_not_utf8",
            "Verified file is not valid UTF-8 text within the bounded read.",
        ) from exc

    content_sha = hashlib.sha256(bounded).hexdigest()

    action_event = store.append_event(
        result_event.project_id,
        EventType.ACTION,
        {
            "kind": "verified_workspace_text_read",
            "capability_id": VERIFIED_TEXT_READ_CAPABILITY_ID,
            "capability_version": VERIFIED_TEXT_READ_VERSION,
            "workspace_result_event_id": workspace_result_event_id,
            "path_identity_sha256": path_identity_sha256,
            "project_id": project_id,
            "relative_path": relative_path,
            "max_bytes": max_bytes,
        },
        actor_kind="orion",
        actor_id="verified-text-read-dispatch",
        task_id=task_id,
        parent_event_id=workspace_result_event_id,
    )

    evidence_event = store.append_event(
        result_event.project_id,
        EventType.EVIDENCE,
        {
            "kind": "verified_workspace_text_evidence",
            "workspace_result_event_id": workspace_result_event_id,
            "action_event_id": action_event.event_id,
            "path_identity_sha256": path_identity_sha256,
            "project_id": project_id,
            "project_name": current.name,
            "repo_identity": current.repo_identity,
            "revision": current.revision,
            "relative_path": relative_path,
            "trust_class": current.trust_class.value,
            "no_cloud": current.no_cloud,
            "license_state": current.license_state,
            "registry_version": current.version,
            "registry_sha256": current.record_sha256,
            "bytes_read": len(bounded),
            "truncated": truncated,
            "content_sha256": content_sha,
        },
        actor_kind="orion",
        actor_id="verified-text-evidence-normalizer",
        task_id=task_id,
        parent_event_id=action_event.event_id,
    )

    final_event = store.append_event(
        result_event.project_id,
        EventType.RESULT,
        {
            "kind": "verified_workspace_text_result",
            "workspace_result_event_id": workspace_result_event_id,
            "action_event_id": action_event.event_id,
            "evidence_event_id": evidence_event.event_id,
            "project_id": project_id,
            "project_name": current.name,
            "repo_identity": current.repo_identity,
            "revision": current.revision,
            "relative_path": relative_path,
            "path_identity_sha256": path_identity_sha256,
            "trust_class": current.trust_class.value,
            "no_cloud": current.no_cloud,
            "license_state": current.license_state,
            "registry_version": current.version,
            "registry_sha256": current.record_sha256,
            "content_sha256": content_sha,
            "bytes_read": len(bounded),
            "truncated": truncated,
            "text": text,
            "absolute_root_exposed": False,
            "authority": "verified_read_only_evidence",
        },
        actor_kind="orion",
        actor_id="verified-text-deterministic-verifier",
        task_id=task_id,
        parent_event_id=evidence_event.event_id,
    )

    return VerifiedTextReadResult(
        action_event_id=action_event.event_id,
        evidence_event_id=evidence_event.event_id,
        result_event_id=final_event.event_id,
        project_id=project_id,
        relative_path=relative_path,
        path_identity_sha256=path_identity_sha256,
        content_sha256=content_sha,
        text=text,
        bytes_read=len(bounded),
        truncated=truncated,
    )


__all__ = [
    "VERIFIED_TEXT_READ_CAPABILITY_ID",
    "VERIFIED_TEXT_READ_VERSION",
    "VerifiedTextReadResult",
    "read_verified_workspace_text",
    "verified_text_read_tool_spec",
]
