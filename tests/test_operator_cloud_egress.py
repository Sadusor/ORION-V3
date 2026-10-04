from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from orion_v3.operator import (
    OperatorControlDenied,
    OperatorControlPlane,
    build_cloud_egress_packet,
    queue_cloud_review_from_egress,
    record_cloud_egress_decision,
)
from orion_v3.state import EventType, OrionStateStore


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_store(tmp_path: Path):
    store = OrionStateStore(tmp_path / "orion.db")
    store.initialize()
    project = store.create_project("Cloud Egress", project_id="egress-project")
    task = store.create_task(
        project.project_id,
        "Compare verified project evidence in the cloud.",
        task_id="egress-task",
    )
    control = OperatorControlPlane(store)
    control.initialize()
    return store, control, project, task


def append_verified_text(
    store: OrionStateStore,
    *,
    project_id: str,
    task_id: str,
    logical_project_id: str,
    project_name: str,
    relative_path: str,
    text: str,
    no_cloud: bool,
    trust_class: str = "owner_project",
    license_state: str = "OWNER",
):
    return store.append_event(
        project_id,
        EventType.RESULT,
        {
            "kind": "verified_workspace_text_result",
            "workspace_result_event_id": "fixture-workspace-result",
            "action_event_id": "fixture-read-action",
            "evidence_event_id": "fixture-read-evidence",
            "project_id": logical_project_id,
            "project_name": project_name,
            "repo_identity": f"https://example.invalid/{logical_project_id}.git",
            "revision": logical_project_id + "-sha",
            "relative_path": relative_path,
            "path_identity_sha256": _sha(
                logical_project_id + ":" + relative_path
            ),
            "trust_class": trust_class,
            "no_cloud": no_cloud,
            "license_state": license_state,
            "registry_version": 1,
            "registry_sha256": _sha(logical_project_id + ":registry"),
            "content_sha256": _sha(text),
            "bytes_read": len(text.encode("utf-8")),
            "truncated": False,
            "text": text,
            "absolute_root_exposed": False,
            "authority": "verified_read_only_evidence",
        },
        actor_kind="orion",
        actor_id="verified-text-deterministic-verifier",
        task_id=task_id,
    )


def test_no_cloud_content_is_excluded_from_prompt_and_canonical_egress(tmp_path: Path):
    store, control, project, task = make_store(tmp_path)
    allowed_marker = "ALLOWED_CLOUD_SENTINEL_4F7C"
    private_marker = "PRIVATE_NO_CLOUD_SENTINEL_91AB"

    allowed = append_verified_text(
        store,
        project_id=project.project_id,
        task_id=task.task_id,
        logical_project_id="project-public",
        project_name="Public Project",
        relative_path="src/public.py",
        text="def public():\n    return '" + allowed_marker + "'\n",
        no_cloud=False,
    )
    private = append_verified_text(
        store,
        project_id=project.project_id,
        task_id=task.task_id,
        logical_project_id="project-private",
        project_name="Private Project",
        relative_path="src/private.py",
        text="def private():\n    return '" + private_marker + "'\n",
        no_cloud=True,
        trust_class="shared_or_client",
        license_state="PRIVATE",
    )

    packet = build_cloud_egress_packet(
        store,
        task_id=task.task_id,
        verified_text_result_event_ids=[allowed.event_id, private.event_id],
        provider_id="groq",
        model_id="openai/gpt-oss-120b",
        purpose="Compare the permitted implementation and identify risks.",
    )

    assert len(packet.included) == 1
    assert packet.included[0].project_id == "project-public"
    assert len(packet.excluded) == 1
    assert packet.excluded[0]["project_id"] == "project-private"
    assert packet.excluded[0]["reason"] == "no_cloud_policy"
    assert allowed_marker in packet.prompt
    assert private_marker not in packet.prompt
    assert "EXCLUDED_BY_LOCAL_POLICY=no_cloud" in packet.prompt
    assert packet.prompt_sha256 == _sha(packet.prompt)
    assert packet.prompt == packet.prompt.strip()

    decision = record_cloud_egress_decision(store, packet=packet)
    event = store.get_event(decision.event_id)
    assert event is not None
    assert event.event_type == EventType.DECISION
    assert event.payload["authority"] == "orion_deterministic_policy"
    assert event.payload["provider_id"] == "groq"
    assert event.payload["model_id"] == "openai/gpt-oss-120b"
    assert decision.included_project_ids == ("project-public",)
    assert decision.excluded_project_ids == ("project-private",)

    decision_encoded = repr(event.payload)
    assert private_marker not in decision_encoded
    assert allowed_marker not in decision_encoded

    queued = queue_cloud_review_from_egress(
        control,
        packet=packet,
        egress_decision_event_id=decision.event_id,
        requested_by="qwen35-9b-orion",
    )
    request_event = store.get_event(queued.request.event_id)
    assert request_event is not None
    assert request_event.parent_event_id == decision.event_id
    assert queued.request.task == packet.prompt
    assert private_marker not in queued.request.task
    assert allowed_marker in queued.request.task


def test_all_no_cloud_evidence_blocks_egress(tmp_path: Path):
    store, _, project, task = make_store(tmp_path)
    private = append_verified_text(
        store,
        project_id=project.project_id,
        task_id=task.task_id,
        logical_project_id="private-only",
        project_name="Private Only",
        relative_path="secret.py",
        text="TOP_SECRET_NEVER_SEND",
        no_cloud=True,
    )

    with pytest.raises(OperatorControlDenied) as exc:
        build_cloud_egress_packet(
            store,
            task_id=task.task_id,
            verified_text_result_event_ids=[private.event_id],
            provider_id="groq",
            model_id="openai/gpt-oss-120b",
            purpose="Review evidence.",
        )

    assert exc.value.code == "cloud_egress_empty_after_policy"


def test_verified_text_hash_mismatch_blocks_egress(tmp_path: Path):
    store, _, project, task = make_store(tmp_path)
    event = store.append_event(
        project.project_id,
        EventType.RESULT,
        {
            "kind": "verified_workspace_text_result",
            "project_id": "p",
            "project_name": "P",
            "repo_identity": "https://example.invalid/p.git",
            "revision": "sha",
            "relative_path": "a.py",
            "path_identity_sha256": "a" * 64,
            "trust_class": "owner_project",
            "no_cloud": False,
            "license_state": "OWNER",
            "registry_version": 1,
            "registry_sha256": "b" * 64,
            "content_sha256": "0" * 64,
            "bytes_read": 3,
            "truncated": False,
            "text": "abc",
            "absolute_root_exposed": False,
            "authority": "verified_read_only_evidence",
        },
        actor_kind="orion",
        actor_id="fixture",
        task_id=task.task_id,
    )

    with pytest.raises(OperatorControlDenied) as exc:
        build_cloud_egress_packet(
            store,
            task_id=task.task_id,
            verified_text_result_event_ids=[event.event_id],
            provider_id="groq",
            model_id="openai/gpt-oss-120b",
            purpose="Review evidence.",
        )

    assert exc.value.code == "verified_text_hash_mismatch"


def test_packet_bound_makes_truncation_explicit(tmp_path: Path):
    store, _, project, task = make_store(tmp_path)
    large = append_verified_text(
        store,
        project_id=project.project_id,
        task_id=task.task_id,
        logical_project_id="large-project",
        project_name="Large",
        relative_path="large.py",
        text="X" * 5000,
        no_cloud=False,
    )

    packet = build_cloud_egress_packet(
        store,
        task_id=task.task_id,
        verified_text_result_event_ids=[large.event_id],
        provider_id="groq",
        model_id="openai/gpt-oss-120b",
        purpose="Review bounded evidence.",
        max_total_chars=1800,
    )

    assert packet.packet_truncated is True
    assert len(packet.included) == 1
    assert packet.included[0].packet_truncated is True
    assert len(packet.prompt) <= 1800
    assert packet.included[0].included_text_sha256 == _sha(
        packet.included[0].included_text
    )


def test_queue_rejects_packet_not_matching_egress_decision(tmp_path: Path):
    store, control, project, task = make_store(tmp_path)
    first = append_verified_text(
        store,
        project_id=project.project_id,
        task_id=task.task_id,
        logical_project_id="a",
        project_name="A",
        relative_path="a.py",
        text="A",
        no_cloud=False,
    )
    second = append_verified_text(
        store,
        project_id=project.project_id,
        task_id=task.task_id,
        logical_project_id="b",
        project_name="B",
        relative_path="b.py",
        text="B",
        no_cloud=False,
    )
    packet_a = build_cloud_egress_packet(
        store,
        task_id=task.task_id,
        verified_text_result_event_ids=[first.event_id],
        provider_id="groq",
        model_id="openai/gpt-oss-120b",
        purpose="Review A.",
    )
    decision = record_cloud_egress_decision(store, packet=packet_a)
    packet_b = build_cloud_egress_packet(
        store,
        task_id=task.task_id,
        verified_text_result_event_ids=[second.event_id],
        provider_id="groq",
        model_id="openai/gpt-oss-120b",
        purpose="Review B.",
    )

    with pytest.raises(OperatorControlDenied) as exc:
        queue_cloud_review_from_egress(
            control,
            packet=packet_b,
            egress_decision_event_id=decision.event_id,
            requested_by="qwen35-9b-orion",
        )

    assert exc.value.code == "cloud_egress_packet_mismatch"


def test_identical_prompt_under_new_egress_decision_does_not_reuse_old_request(tmp_path: Path):
    store, control, project, task = make_store(tmp_path)
    source = append_verified_text(
        store,
        project_id=project.project_id,
        task_id=task.task_id,
        logical_project_id="a",
        project_name="A",
        relative_path="a.py",
        text="same bounded evidence",
        no_cloud=False,
    )
    packet = build_cloud_egress_packet(
        store,
        task_id=task.task_id,
        verified_text_result_event_ids=[source.event_id],
        provider_id="groq",
        model_id="openai/gpt-oss-120b",
        purpose="Review same packet.",
    )
    decision_one = record_cloud_egress_decision(store, packet=packet)
    request_one = queue_cloud_review_from_egress(
        control,
        packet=packet,
        egress_decision_event_id=decision_one.event_id,
        requested_by="orion",
    )
    decision_two = record_cloud_egress_decision(store, packet=packet)
    request_two = queue_cloud_review_from_egress(
        control,
        packet=packet,
        egress_decision_event_id=decision_two.event_id,
        requested_by="orion",
    )

    assert request_one.duplicate is False
    assert request_two.duplicate is False
    assert request_one.request.request_id != request_two.request.request_id
    assert request_one.request.request_sha256 != request_two.request.request_sha256
    assert store.get_event(request_one.request.event_id).parent_event_id == decision_one.event_id
    assert store.get_event(request_two.request.event_id).parent_event_id == decision_two.event_id
