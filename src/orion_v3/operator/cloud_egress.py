from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from orion_v3.state import EventType, OrionStateStore

from .control import CloudQueueResult, OperatorControlDenied, OperatorControlPlane


@dataclass(frozen=True)
class CloudEgressItem:
    result_event_id: str
    project_id: str
    project_name: str
    repo_identity: str | None
    revision: str | None
    relative_path: str
    path_identity_sha256: str
    content_sha256: str
    trust_class: str
    license_state: str
    no_cloud: bool
    bytes_read: int
    source_truncated: bool
    included_text: str
    included_text_sha256: str
    packet_truncated: bool


@dataclass(frozen=True)
class CloudEgressPacket:
    task_id: str
    provider_id: str
    model_id: str
    purpose: str
    included: tuple[CloudEgressItem, ...]
    excluded: tuple[Mapping[str, Any], ...]
    prompt: str
    prompt_sha256: str
    packet_truncated: bool


@dataclass(frozen=True)
class CloudEgressDecision:
    event_id: str
    packet_sha256: str
    included_project_ids: tuple[str, ...]
    excluded_project_ids: tuple[str, ...]
    packet_truncated: bool


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _require_verified_text_result(
    store: OrionStateStore,
    *,
    task_id: str,
    result_event_id: str,
) -> tuple[Any, dict[str, Any]]:
    event = store.get_event(result_event_id)
    if event is None:
        raise OperatorControlDenied(
            "unknown_verified_text_result",
            "Verified text RESULT does not exist.",
        )
    if event.task_id != task_id:
        raise OperatorControlDenied(
            "wrong_task",
            "Verified text RESULT belongs to another task.",
        )
    if event.event_type != EventType.RESULT:
        raise OperatorControlDenied(
            "invalid_verified_text_result",
            "Cloud egress requires RESULT evidence.",
        )
    payload = dict(event.payload)
    if payload.get("kind") != "verified_workspace_text_result":
        raise OperatorControlDenied(
            "invalid_verified_text_result",
            "RESULT is not verified workspace text.",
        )
    if payload.get("authority") != "verified_read_only_evidence":
        raise OperatorControlDenied(
            "invalid_verified_text_authority",
            "Verified text RESULT authority marker is invalid.",
        )
    if payload.get("absolute_root_exposed") is not False:
        raise OperatorControlDenied(
            "unsafe_verified_text_result",
            "Verified text RESULT is not safe for egress processing.",
        )
    text = payload.get("text")
    if not isinstance(text, str):
        raise OperatorControlDenied(
            "invalid_verified_text_result",
            "Verified text RESULT lacks text.",
        )
    if _sha256_text(text) != str(payload.get("content_sha256") or ""):
        raise OperatorControlDenied(
            "verified_text_hash_mismatch",
            "Verified text content hash no longer matches RESULT.",
        )
    return event, payload


def build_cloud_egress_packet(
    store: OrionStateStore,
    *,
    task_id: str,
    verified_text_result_event_ids: Iterable[str],
    provider_id: str,
    model_id: str,
    purpose: str,
    max_total_chars: int = 12000,
) -> CloudEgressPacket:
    """Build a bounded cloud packet from verified local evidence.

    no_cloud evidence is represented only as excluded metadata. Its text is
    never copied into the rendered cloud prompt.
    """
    provider_id = str(provider_id or "").strip()
    model_id = str(model_id or "").strip()
    purpose = str(purpose or "").strip()
    if not provider_id or not model_id or not purpose:
        raise OperatorControlDenied(
            "invalid_cloud_egress_request",
            "provider_id, model_id and purpose must be non-empty.",
        )
    if max_total_chars < 256 or max_total_chars > 100000:
        raise OperatorControlDenied(
            "invalid_cloud_egress_bound",
            "max_total_chars must be between 256 and 100000.",
        )

    ids = [str(item or "").strip() for item in verified_text_result_event_ids]
    if not ids or any(not item for item in ids):
        raise OperatorControlDenied(
            "invalid_cloud_egress_request",
            "At least one verified text RESULT is required.",
        )
    if len(set(ids)) != len(ids):
        raise OperatorControlDenied(
            "duplicate_cloud_egress_source",
            "Verified text RESULT IDs must be unique.",
        )

    raw_included: list[tuple[str, dict[str, Any]]] = []
    excluded: list[Mapping[str, Any]] = []

    for result_event_id in ids:
        _, payload = _require_verified_text_result(
            store,
            task_id=task_id,
            result_event_id=result_event_id,
        )
        metadata = {
            "result_event_id": result_event_id,
            "project_id": str(payload.get("project_id") or ""),
            "project_name": str(payload.get("project_name") or ""),
            "repo_identity": payload.get("repo_identity"),
            "revision": payload.get("revision"),
            "relative_path": str(payload.get("relative_path") or ""),
            "path_identity_sha256": str(payload.get("path_identity_sha256") or ""),
            "content_sha256": str(payload.get("content_sha256") or ""),
            "trust_class": str(payload.get("trust_class") or ""),
            "license_state": str(payload.get("license_state") or ""),
            "no_cloud": bool(payload.get("no_cloud")),
            "bytes_read": int(payload.get("bytes_read") or 0),
            "source_truncated": bool(payload.get("truncated")),
        }
        if metadata["no_cloud"]:
            excluded.append(
                {
                    **metadata,
                    "reason": "no_cloud_policy",
                }
            )
        else:
            raw_included.append((str(payload["text"]), metadata))

    if not raw_included:
        raise OperatorControlDenied(
            "cloud_egress_empty_after_policy",
            "All selected evidence is excluded by local cloud-egress policy.",
        )

    header = (
        "ORION V3 CROSS-PROJECT CLOUD REVIEW\n\n"
        "AUTHORITY FRAME\n"
        "- This packet contains bounded local evidence selected by ORION.\n"
        "- You are advisory only.\n"
        "- You have no tools, filesystem, shell, browser, approval, write, read, "
        "project-selection, task-mutation or Hand authority.\n"
        "- Do not claim that any action was executed.\n"
        "- Do not request or infer hidden local paths.\n\n"
        f"PROVIDER: {provider_id}\n"
        f"MODEL: {model_id}\n"
        f"PURPOSE: {purpose}\n\n"
    )
    excluded_lines = []
    for item in excluded:
        excluded_lines.append(
            "- "
            + item["project_name"]
            + " ["
            + item["project_id"]
            + "] "
            + str(item["relative_path"])
            + " EXCLUDED_BY_LOCAL_POLICY=no_cloud"
        )
    excluded_block = (
        "LOCAL POLICY EXCLUSIONS\n"
        + ("\n".join(excluded_lines) if excluded_lines else "- none")
        + "\n\n"
    )
    review_request = (
        "\nREVIEW REQUEST\n"
        "Analyze only the permitted evidence above. Mention any policy-excluded "
        "project only as unavailable evidence. Return concise headings: FINDINGS, "
        "RISKS, RECOMMENDATION.\n"
    )
    evidence_prefix = "PERMITTED EVIDENCE\n\n"
    remaining = (
        max_total_chars
        - len(header)
        - len(excluded_block)
        - len(evidence_prefix)
        - len(review_request)
    )
    if remaining < 1:
        raise OperatorControlDenied(
            "cloud_egress_bound_too_small",
            "Cloud egress bound cannot fit required policy framing.",
        )

    included_items: list[CloudEgressItem] = []
    evidence_blocks: list[str] = []
    packet_truncated = False

    for text, meta in raw_included:
        item_header = (
            "EVIDENCE ITEM\n"
            f"project_id: {meta['project_id']}\n"
            f"project_name: {meta['project_name']}\n"
            f"repo_identity: {meta['repo_identity']}\n"
            f"revision: {meta['revision']}\n"
            f"relative_path: {meta['relative_path']}\n"
            f"path_identity_sha256: {meta['path_identity_sha256']}\n"
            f"source_content_sha256: {meta['content_sha256']}\n"
            f"trust_class: {meta['trust_class']}\n"
            f"license_state: {meta['license_state']}\n"
            f"source_truncated: {str(meta['source_truncated']).lower()}\n"
            "authority: evidence_only\n"
            "CONTENT_BEGIN\n"
        )
        footer = "\nCONTENT_END\n"
        room_for_text = remaining - len(item_header) - len(footer)
        if room_for_text <= 0:
            packet_truncated = True
            break
        included_text = text[:room_for_text]
        item_truncated = len(included_text) < len(text)
        packet_truncated = packet_truncated or item_truncated
        block = item_header + included_text + footer
        evidence_blocks.append(block)
        remaining -= len(block)
        included_items.append(
            CloudEgressItem(
                result_event_id=meta["result_event_id"],
                project_id=meta["project_id"],
                project_name=meta["project_name"],
                repo_identity=meta["repo_identity"],
                revision=meta["revision"],
                relative_path=meta["relative_path"],
                path_identity_sha256=meta["path_identity_sha256"],
                content_sha256=meta["content_sha256"],
                trust_class=meta["trust_class"],
                license_state=meta["license_state"],
                no_cloud=False,
                bytes_read=meta["bytes_read"],
                source_truncated=meta["source_truncated"],
                included_text=included_text,
                included_text_sha256=_sha256_text(included_text),
                packet_truncated=item_truncated,
            )
        )
        if item_truncated:
            break

    if not included_items:
        raise OperatorControlDenied(
            "cloud_egress_bound_too_small",
            "Cloud egress bound cannot fit any permitted evidence.",
        )
    if len(included_items) < len(raw_included):
        packet_truncated = True

    prompt = (
        header
        + excluded_block
        + evidence_prefix
        + "\n".join(evidence_blocks)
        + review_request
    )
    if len(prompt) > max_total_chars:
        raise OperatorControlDenied(
            "cloud_egress_internal_bound_failure",
            "Rendered cloud prompt exceeded deterministic bound.",
        )

    return CloudEgressPacket(
        task_id=task_id,
        provider_id=provider_id,
        model_id=model_id,
        purpose=purpose,
        included=tuple(included_items),
        excluded=tuple(excluded),
        prompt=prompt,
        prompt_sha256=_sha256_text(prompt),
        packet_truncated=packet_truncated,
    )


def record_cloud_egress_decision(
    store: OrionStateStore,
    *,
    packet: CloudEgressPacket,
) -> CloudEgressDecision:
    task = store.get_task(packet.task_id)
    if task is None:
        raise OperatorControlDenied("unknown_task", "Task does not exist.")

    payload = {
        "kind": "cloud_egress_policy_decision",
        "authority": "orion_deterministic_policy",
        "provider_id": packet.provider_id,
        "model_id": packet.model_id,
        "purpose": packet.purpose,
        "prompt_sha256": packet.prompt_sha256,
        "packet_truncated": packet.packet_truncated,
        "included": [
            {
                "result_event_id": item.result_event_id,
                "project_id": item.project_id,
                "project_name": item.project_name,
                "repo_identity": item.repo_identity,
                "revision": item.revision,
                "relative_path": item.relative_path,
                "path_identity_sha256": item.path_identity_sha256,
                "source_content_sha256": item.content_sha256,
                "included_text_sha256": item.included_text_sha256,
                "trust_class": item.trust_class,
                "license_state": item.license_state,
                "source_truncated": item.source_truncated,
                "packet_truncated": item.packet_truncated,
            }
            for item in packet.included
        ],
        "excluded": [
            {
                "result_event_id": item["result_event_id"],
                "project_id": item["project_id"],
                "project_name": item["project_name"],
                "repo_identity": item["repo_identity"],
                "revision": item["revision"],
                "relative_path": item["relative_path"],
                "path_identity_sha256": item["path_identity_sha256"],
                "content_sha256": item["content_sha256"],
                "trust_class": item["trust_class"],
                "license_state": item["license_state"],
                "reason": item["reason"],
            }
            for item in packet.excluded
        ],
    }
    packet_sha = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    event = store.append_event(
        task.project_id,
        EventType.DECISION,
        {
            **payload,
            "packet_sha256": packet_sha,
        },
        actor_kind="orion",
        actor_id="cloud-egress-policy",
        task_id=packet.task_id,
    )
    return CloudEgressDecision(
        event_id=event.event_id,
        packet_sha256=packet_sha,
        included_project_ids=tuple(item.project_id for item in packet.included),
        excluded_project_ids=tuple(
            str(item["project_id"]) for item in packet.excluded
        ),
        packet_truncated=packet.packet_truncated,
    )


def queue_cloud_review_from_egress(
    control: OperatorControlPlane,
    *,
    packet: CloudEgressPacket,
    egress_decision_event_id: str,
    requested_by: str,
) -> CloudQueueResult:
    decision = control.store.get_event(egress_decision_event_id)
    if decision is None or decision.task_id != packet.task_id:
        raise OperatorControlDenied(
            "invalid_cloud_egress_decision",
            "Cloud egress decision is missing or belongs to another task.",
        )
    if decision.event_type != EventType.DECISION:
        raise OperatorControlDenied(
            "invalid_cloud_egress_decision",
            "Cloud egress parent is not a DECISION.",
        )
    if decision.payload.get("kind") != "cloud_egress_policy_decision":
        raise OperatorControlDenied(
            "invalid_cloud_egress_decision",
            "Cloud egress parent has the wrong kind.",
        )
    if decision.payload.get("authority") != "orion_deterministic_policy":
        raise OperatorControlDenied(
            "invalid_cloud_egress_decision",
            "Cloud egress decision authority is invalid.",
        )
    if decision.payload.get("prompt_sha256") != packet.prompt_sha256:
        raise OperatorControlDenied(
            "cloud_egress_packet_mismatch",
            "Cloud packet no longer matches the canonical egress decision.",
        )

    return control.queue_cloud_specialist(
        packet.task_id,
        specialty="review",
        task=packet.prompt,
        requested_by=requested_by,
        parent_event_id=egress_decision_event_id,
    )


__all__ = [
    "CloudEgressDecision",
    "CloudEgressItem",
    "CloudEgressPacket",
    "build_cloud_egress_packet",
    "queue_cloud_review_from_egress",
    "record_cloud_egress_decision",
]
