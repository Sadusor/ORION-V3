from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPENJARVIS_SRC = ROOT / "external" / "OpenJarvis" / "src"
if not OPENJARVIS_SRC.exists():
    raise SystemExit("Pinned OpenJarvis donor missing; run fetch_openjarvis.ps1 first.")
sys.path.insert(0, str(OPENJARVIS_SRC))
sys.path.insert(0, str(ROOT / "src"))

from orion_v3.operator import (
    OperatorControlPlane,
    build_cloud_egress_packet,
    call_openai_compatible_advisory,
    execute_workspace_search,
    groq_gptoss_120b_spec,
    propose_workspace_search,
    queue_cloud_review_from_egress,
    read_verified_workspace_text,
    record_cloud_egress_decision,
)
from orion_v3.state import EventType, OrionStateStore
from orion_v3.workspaces import (
    ArchiveState,
    ReadPolicy,
    TrustClass,
    WorkspaceRegistry,
    WritePolicy,
)


PUBLIC_FILE = "__ORION_RUN059_PUBLIC__.py"
PRIVATE_FILE = "__ORION_RUN059_PRIVATE__.py"
PUBLIC_SENTINEL = "ALLOWED_CLOUD_EVIDENCE_7A31"
PRIVATE_SENTINEL = "PRIVATE_NO_CLOUD_SENTINEL_C4D9"


def register(
    registry: WorkspaceRegistry,
    *,
    project_id: str,
    name: str,
    root: Path,
    revision: str,
    no_cloud: bool,
    trust_class: TrustClass,
    license_state: str,
):
    return registry.upsert_project(
        actor_kind="owner",
        owner_id="owner-run059",
        project_id=project_id,
        name=name,
        trusted_root=root,
        trust_class=trust_class,
        repo_identity=f"https://example.invalid/{project_id}.git",
        archive_state=ArchiveState.ACTIVE,
        read_policy=ReadPolicy.ALLOWED,
        write_policy=WritePolicy.OWNER_APPROVAL,
        no_cloud=no_cloud,
        license_state=license_state,
        revision=revision,
    )


def main() -> int:
    print("V3_RUN_ID> V3-RUN-059R")
    print("ORION_CROSS_PROJECT_CLOUD_EGRESS> START")
    print("MODE> verified local evidence -> no_cloud filter -> canonical egress decision -> real Groq REVIEW")
    print("PROVIDER> groq")
    print("REQUESTED_MODEL> openai/gpt-oss-120b")
    print("AUTHORITY> cloud advisory_only; tools=false; hands=false; project-selection=false")

    with tempfile.TemporaryDirectory(prefix="orion-run059-") as td:
        temp = Path(td)
        public_root = temp / "projects" / "public"
        private_root = temp / "projects" / "private"
        public_root.mkdir(parents=True)
        private_root.mkdir(parents=True)

        public_text = (
            "def candidate_solution():\n"
            f"    return '{PUBLIC_SENTINEL}'\n"
        )
        private_text = (
            "def client_secret_solution():\n"
            f"    return '{PRIVATE_SENTINEL}'\n"
        )
        (public_root / PUBLIC_FILE).write_bytes(public_text.encode("utf-8"))
        (private_root / PRIVATE_FILE).write_bytes(private_text.encode("utf-8"))

        store = OrionStateStore(temp / "orion.db")
        store.initialize()
        try:
            state_project = store.create_project("RUN-059", project_id="run059-state")
            task = store.create_task(
                state_project.project_id,
                "Compare locally verified implementations using a bounded cloud reviewer.",
                task_id="run059-task",
            )
            registry = WorkspaceRegistry(store)
            registry.initialize()
            register(
                registry,
                project_id="project-public",
                name="Public Owner Project",
                root=public_root,
                revision="public-run059-a",
                no_cloud=False,
                trust_class=TrustClass.OWNER_PROJECT,
                license_state="OWNER",
            )
            register(
                registry,
                project_id="project-private",
                name="Private Client Project",
                root=private_root,
                revision="private-run059-a",
                no_cloud=True,
                trust_class=TrustClass.SHARED_OR_CLIENT,
                license_state="PRIVATE",
            )

            control = OperatorControlPlane(store)
            control.initialize()

            proposal = propose_workspace_search(
                store,
                registry,
                task_id=task.task_id,
                exact_names=[PUBLIC_FILE, PRIVATE_FILE],
                scope_token="registered_projects",
                proposed_by="deterministic-run059",
            )
            search = execute_workspace_search(
                store,
                registry,
                task_id=task.task_id,
                proposal_event_id=proposal.event_id,
            )
            if search.verified_result.get("match_count") != 2:
                raise RuntimeError("expected exactly two verified cross-project matches")
            print("LOCAL_CROSS_PROJECT_SEARCH> PASS 2_MATCHES")

            public_match = next(
                item for item in search.verified_result["matches"]
                if item["project_id"] == "project-public"
            )
            private_match = next(
                item for item in search.verified_result["matches"]
                if item["project_id"] == "project-private"
            )
            if public_match["no_cloud"] is not False:
                raise RuntimeError("public fixture cloud policy mismatch")
            if private_match["no_cloud"] is not True:
                raise RuntimeError("private fixture no_cloud policy missing")
            print("LOCAL_POLICY_METADATA> PASS")

            public_read = read_verified_workspace_text(
                store,
                registry,
                task_id=task.task_id,
                workspace_result_event_id=search.result_event_id,
                path_identity_sha256=public_match["path_identity_sha256"],
                max_bytes=4096,
            )
            private_read = read_verified_workspace_text(
                store,
                registry,
                task_id=task.task_id,
                workspace_result_event_id=search.result_event_id,
                path_identity_sha256=private_match["path_identity_sha256"],
                max_bytes=4096,
            )
            if PUBLIC_SENTINEL not in public_read.text:
                raise RuntimeError("public local content read mismatch")
            if PRIVATE_SENTINEL not in private_read.text:
                raise RuntimeError("private local content read mismatch")
            print("LOCAL_VERIFIED_TEXT_READS> PASS 2")
            print("LOCAL_READ_AUTHORIZATION_INCLUDES_NO_CLOUD> PASS")

            provider = groq_gptoss_120b_spec()
            packet = build_cloud_egress_packet(
                store,
                task_id=task.task_id,
                verified_text_result_event_ids=[
                    public_read.result_event_id,
                    private_read.result_event_id,
                ],
                provider_id=provider.provider_id,
                model_id=provider.model_id,
                purpose=(
                    "Review the permitted implementation for correctness risks. "
                    "A second project may be excluded by local policy; do not infer its contents."
                ),
                max_total_chars=12000,
            )
            if [item.project_id for item in packet.included] != ["project-public"]:
                raise RuntimeError("eligible project inclusion mismatch")
            if [item["project_id"] for item in packet.excluded] != ["project-private"]:
                raise RuntimeError("no_cloud project exclusion mismatch")
            if packet.excluded[0]["reason"] != "no_cloud_policy":
                raise RuntimeError("no_cloud exclusion reason mismatch")
            if PUBLIC_SENTINEL not in packet.prompt:
                raise RuntimeError("permitted content missing from cloud packet")
            if PRIVATE_SENTINEL in packet.prompt:
                raise RuntimeError("no_cloud content leaked into cloud packet")
            if str(public_root.resolve()) in packet.prompt or str(private_root.resolve()) in packet.prompt:
                raise RuntimeError("absolute trusted root leaked into cloud packet")
            if packet.packet_truncated:
                raise RuntimeError("small RUN-059 packet unexpectedly truncated")
            print("NO_CLOUD_CONTENT_EXCLUSION> PASS")
            print("CLOUD_PACKET_INCLUDED_PROJECTS> project-public")
            print("CLOUD_PACKET_EXCLUDED_PROJECTS> project-private")
            print("PRIVATE_SENTINEL_IN_CLOUD_PACKET> 0")
            print("TRUSTED_ROOT_IN_CLOUD_PACKET> 0")
            print("CLOUD_PACKET_TRUNCATED> false")

            decision = record_cloud_egress_decision(store, packet=packet)
            decision_event = store.get_event(decision.event_id)
            if decision_event is None:
                raise RuntimeError("egress decision event missing")
            if decision_event.event_type != EventType.DECISION:
                raise RuntimeError("egress policy did not create DECISION")
            if decision_event.payload.get("authority") != "orion_deterministic_policy":
                raise RuntimeError("egress decision authority mismatch")
            encoded_decision = json.dumps(
                decision_event.payload,
                ensure_ascii=False,
                sort_keys=True,
            )
            if PRIVATE_SENTINEL in encoded_decision or PUBLIC_SENTINEL in encoded_decision:
                raise RuntimeError("raw code content leaked into egress audit decision")
            if decision.included_project_ids != ("project-public",):
                raise RuntimeError("egress decision included-project audit mismatch")
            if decision.excluded_project_ids != ("project-private",):
                raise RuntimeError("egress decision excluded-project audit mismatch")
            print("OWNER_VISIBLE_EGRESS_DECISION> PASS")
            print("EGRESS_DECISION_RAW_CODE_CONTENT> 0")

            queued = queue_cloud_review_from_egress(
                control,
                packet=packet,
                egress_decision_event_id=decision.event_id,
                requested_by="orion-egress-dispatch",
            )
            request = queued.request
            request_event = store.get_event(request.event_id)
            if request_event is None:
                raise RuntimeError("cloud request event missing")
            if request_event.parent_event_id != decision.event_id:
                raise RuntimeError("cloud request not causally parented to egress decision")
            if request.task != packet.prompt:
                raise RuntimeError("queued cloud request changed egress packet")
            if PRIVATE_SENTINEL in request.task:
                raise RuntimeError("no_cloud content entered queued provider request")
            print("EGRESS_DECISION_TO_CLOUD_REQUEST_CAUSAL_LINK> PASS")

            response = call_openai_compatible_advisory(provider, request.task)
            print("PROVIDER_STATUS> " + response.status)
            print("SERVED_MODEL> " + str(response.served_model))
            print("PROVIDER_LATENCY_SECONDS> " + str(response.elapsed_seconds))
            print("PROMPT_SHA256> " + response.prompt_sha256)
            print("PROVIDER_RESPONSE_SHA256> " + response.response_sha256)

            if response.status != "PASS":
                raise RuntimeError("live cloud provider did not PASS: " + response.reason)
            if response.served_model != provider.model_id:
                raise RuntimeError("served model does not exactly match requested model")
            if response.prompt_sha256 != packet.prompt_sha256:
                raise RuntimeError("provider prompt hash changed from canonical egress packet")
            if not response.external_message_id:
                raise RuntimeError("provider response lacks external message id")
            if not response.response_text.strip():
                raise RuntimeError("provider returned empty advisory response")
            print("REAL_CLOUD_EGRESS_PROMPT_BINDING> PASS")
            print("PRIVATE_SENTINEL_SENT_TO_PROVIDER> 0")

            ingested = control.ingest_cloud_specialist_response(
                request.request_id,
                source_system="groq-openai-compatible",
                external_message_id=response.external_message_id,
                provider_id=provider.provider_id,
                model_id=provider.model_id,
                response_text=response.response_text,
            )
            review = store.get_event(ingested.event_id)
            if review is None:
                raise RuntimeError("cloud REVIEW event missing")
            if review.event_type != EventType.REVIEW:
                raise RuntimeError("cloud response is not REVIEW")
            if review.parent_event_id != request.event_id:
                raise RuntimeError("cloud REVIEW not parented to exact request")
            body = review.payload.get("body") or {}
            if body.get("authority") != "advisory_only":
                raise RuntimeError("cloud REVIEW gained authority")
            if body.get("provider_id") != provider.provider_id:
                raise RuntimeError("cloud REVIEW provider identity mismatch")
            if body.get("model_id") != provider.model_id:
                raise RuntimeError("cloud REVIEW model identity mismatch")
            print("LIVE_CLOUD_REVIEW_INGESTION> PASS")
            print("LIVE_CLOUD_REVIEW_AUTHORITY> advisory_only")

            events = store.list_task_events(state_project.project_id, task.task_id, limit=100)
            idx = next(
                i for i, event in enumerate(events)
                if event.event_id == decision.event_id
            )
            cloud_tail = events[idx:]
            if [event.event_type for event in cloud_tail] != [
                EventType.DECISION,
                EventType.PROPOSAL,
                EventType.REVIEW,
            ]:
                raise RuntimeError(
                    "unexpected egress/request/review event tail: "
                    + repr([event.event_type.value for event in cloud_tail])
                )
            if any(event.event_type == EventType.ACTION for event in cloud_tail):
                raise RuntimeError("cloud egress/review minted ACTION authority")
            print("CLOUD_EGRESS_DECISIONS_CREATED> 1_POLICY_DECISION")
            print("CLOUD_REVIEW_ACTIONS_CREATED> 0")
            print("CLOUD_HAND_EXECUTIONS> 0")
            print("CLOUD_TOOLS_ENABLED> 0")
            print("CLOUD_FALLBACK_SUBSTITUTIONS> 0")

            summary = {
                "schema": "orion.v3.cross-project-cloud-egress.v0",
                "run_id": "V3-RUN-059R",
                "provider": provider.provider_id,
                "requested_model": provider.model_id,
                "served_model": response.served_model,
                "included_project_ids": list(decision.included_project_ids),
                "excluded_project_ids": list(decision.excluded_project_ids),
                "exclusion_reason": "no_cloud_policy",
                "private_sentinel_in_prompt": False,
                "trusted_root_in_prompt": False,
                "packet_truncated": packet.packet_truncated,
                "prompt_sha256": packet.prompt_sha256,
                "provider_prompt_sha256": response.prompt_sha256,
                "provider_response_sha256": response.response_sha256,
                "egress_decision_event_id": decision.event_id,
                "cloud_request_event_id": request.event_id,
                "review_event_id": ingested.event_id,
                "review_authority": "advisory_only",
                "cloud_actions_created": 0,
                "cloud_hand_executions": 0,
                "cloud_tools_enabled": 0,
                "fallback_substitutions": 0,
            }
            print(
                "ORION_CROSS_PROJECT_CLOUD_EGRESS_SUMMARY> "
                + json.dumps(summary, ensure_ascii=False, sort_keys=True)
            )
        finally:
            store.close()

    print("ORION_CROSS_PROJECT_CLOUD_EGRESS> PASS")
    print("STATUS> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
