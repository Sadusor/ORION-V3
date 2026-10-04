from __future__ import annotations

import hashlib
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
    OperatorControlDenied,
    execute_workspace_search,
    propose_workspace_search,
    read_verified_workspace_text,
    verified_text_read_tool_spec,
)
from orion_v3.state import EventType, OrionStateStore
from orion_v3.workspaces import (
    ArchiveState,
    ReadPolicy,
    TrustClass,
    WorkspaceRegistry,
    WritePolicy,
)


TARGET = "__ORION_RUN057_TARGET__.py"
BIG = "__ORION_RUN057_BIG__.txt"


def register(
    registry: WorkspaceRegistry,
    *,
    project_id: str,
    name: str,
    root: Path,
    revision: str,
):
    return registry.upsert_project(
        actor_kind="owner",
        owner_id="owner-run057",
        project_id=project_id,
        name=name,
        trusted_root=root,
        trust_class=TrustClass.OWNER_PROJECT,
        repo_identity=f"https://example.invalid/{project_id}.git",
        archive_state=ArchiveState.ACTIVE,
        read_policy=ReadPolicy.ALLOWED,
        write_policy=WritePolicy.OWNER_APPROVAL,
        no_cloud=False,
        license_state="OWNER",
        revision=revision,
    )


def count_read_actions(store: OrionStateStore, project_id: str, task_id: str) -> int:
    return sum(
        1
        for event in store.list_task_events(project_id, task_id, limit=100)
        if event.event_type == EventType.ACTION
        and event.payload.get("kind") == "verified_workspace_text_read"
    )


def main() -> int:
    print("V3_RUN_ID> V3-RUN-058")
    print("ORION_VERIFIED_TEXT_READ> START")
    print("MODE> verified workspace evidence identity -> bounded current text read")
    print("MODEL_CALLS> 0")
    print("EXTERNAL_PROVIDER_CALLS> 0")

    tool = verified_text_read_tool_spec()
    props = tool["function"]["parameters"]["properties"]
    if set(props) != {"path_identity_sha256"}:
        raise RuntimeError("verified text read exposes model-controlled path/scope")
    print("MODEL_PATH_ARGUMENTS> 0")
    print("MODEL_EVIDENCE_ID_ARGUMENTS> 1")

    with tempfile.TemporaryDirectory(prefix="orion-run057-") as td:
        temp = Path(td)
        alpha_root = temp / "alpha"
        beta_root = temp / "beta"
        alpha_root.mkdir()
        beta_root.mkdir()

        alpha_content = "def solution():\n    return 'alpha verified content'\n"
        beta_content = "def solution():\n    return 'beta verified content'\n"
        big_content = "Z" * 512

        (alpha_root / TARGET).write_bytes(alpha_content.encode("utf-8"))
        (beta_root / TARGET).write_bytes(beta_content.encode("utf-8"))
        (alpha_root / BIG).write_bytes(big_content.encode("utf-8"))

        store = OrionStateStore(temp / "orion.db")
        store.initialize()
        state_project = store.create_project("RUN-057", project_id="run057-state")
        task = store.create_task(
            state_project.project_id,
            "Find and read exact verified workspace text.",
            task_id="run057-task",
        )
        registry = WorkspaceRegistry(store)
        registry.initialize()
        register(
            registry,
            project_id="project-alpha",
            name="Alpha",
            root=alpha_root,
            revision="alpha-057-a",
        )
        register(
            registry,
            project_id="project-beta",
            name="Beta",
            root=beta_root,
            revision="beta-057-a",
        )

        proposal = propose_workspace_search(
            store,
            registry,
            task_id=task.task_id,
            exact_names=[TARGET, BIG],
            scope_token="registered_projects",
            proposed_by="deterministic-run057",
        )
        search = execute_workspace_search(
            store,
            registry,
            task_id=task.task_id,
            proposal_event_id=proposal.event_id,
        )
        if search.verified_result.get("status") != "PASS":
            raise RuntimeError("cross-project prerequisite search did not verify")
        if search.verified_result.get("match_count") != 3:
            raise RuntimeError("expected alpha target + beta target + alpha big evidence")
        print("REAL_WORKSPACE_SEARCH_PREREQUISITE> PASS")
        print("VERIFIED_SEARCH_MATCH_COUNT> 3")

        matches = search.verified_result["matches"]
        alpha_target = next(
            item for item in matches
            if item["project_id"] == "project-alpha" and item["name"] == TARGET
        )
        beta_target = next(
            item for item in matches
            if item["project_id"] == "project-beta" and item["name"] == TARGET
        )
        alpha_big = next(
            item for item in matches
            if item["project_id"] == "project-alpha" and item["name"] == BIG
        )

        read = read_verified_workspace_text(
            store,
            registry,
            task_id=task.task_id,
            workspace_result_event_id=search.result_event_id,
            path_identity_sha256=alpha_target["path_identity_sha256"],
            max_bytes=4096,
        )
        if read.text != alpha_content:
            raise RuntimeError("verified text content mismatch")
        expected_hash = hashlib.sha256(alpha_content.encode("utf-8")).hexdigest()
        if read.content_sha256 != expected_hash:
            raise RuntimeError("verified content hash mismatch")
        if read.truncated:
            raise RuntimeError("small verified text unexpectedly truncated")
        print("EVIDENCE_BOUND_TEXT_READ> PASS")
        print("CONTENT_SHA256> " + read.content_sha256)
        print("CONTENT_TRUNCATED> false")

        read_event = store.get_event(read.result_event_id)
        if read_event is None:
            raise RuntimeError("verified text RESULT missing")
        encoded = json.dumps(read_event.payload, ensure_ascii=False, sort_keys=True)
        if str(alpha_root.resolve()) in encoded or str(beta_root.resolve()) in encoded:
            raise RuntimeError("trusted absolute root leaked into verified text RESULT")
        if "trusted_root" in encoded:
            raise RuntimeError("trusted_root field leaked into verified text RESULT")
        print("VERIFIED_TEXT_ROOT_LEAK> 0")

        before_forged = count_read_actions(
            store,
            state_project.project_id,
            task.task_id,
        )
        forged_blocked = False
        try:
            read_verified_workspace_text(
                store,
                registry,
                task_id=task.task_id,
                workspace_result_event_id=search.result_event_id,
                path_identity_sha256="0" * 64,
            )
        except OperatorControlDenied as exc:
            forged_blocked = exc.code == "unknown_evidence_identity"
        if not forged_blocked:
            raise RuntimeError("forged evidence identity was not blocked")
        after_forged = count_read_actions(
            store,
            state_project.project_id,
            task.task_id,
        )
        if after_forged != before_forged:
            raise RuntimeError("forged evidence identity created a read ACTION")
        print("FORGED_EVIDENCE_ID> BLOCKED")
        print("FORGED_ID_READ_ACTIONS> 0")

        bounded = read_verified_workspace_text(
            store,
            registry,
            task_id=task.task_id,
            workspace_result_event_id=search.result_event_id,
            path_identity_sha256=alpha_big["path_identity_sha256"],
            max_bytes=64,
        )
        if bounded.bytes_read != 64 or not bounded.truncated:
            raise RuntimeError("bounded text read did not report truncation")
        if bounded.text != "Z" * 64:
            raise RuntimeError("bounded text read returned wrong prefix")
        if bounded.content_sha256 != hashlib.sha256(b"Z" * 64).hexdigest():
            raise RuntimeError("bounded content hash mismatch")
        print("BOUNDED_TEXT_READ> PASS")
        print("BOUNDED_BYTES_READ> 64")
        print("BOUNDED_TRUNCATION_VISIBLE> PASS")

        # Change beta after the search. Exact old evidence must not read new bytes.
        before_changed = count_read_actions(
            store,
            state_project.project_id,
            task.task_id,
        )
        (beta_root / TARGET).write_text(
            beta_content + "# changed after search\n",
            encoding="utf-8",
        )
        changed_blocked = False
        try:
            read_verified_workspace_text(
                store,
                registry,
                task_id=task.task_id,
                workspace_result_event_id=search.result_event_id,
                path_identity_sha256=beta_target["path_identity_sha256"],
            )
        except OperatorControlDenied as exc:
            changed_blocked = exc.code == "workspace_file_changed"
        if not changed_blocked:
            raise RuntimeError("file changed after search was not blocked")
        after_changed = count_read_actions(
            store,
            state_project.project_id,
            task.task_id,
        )
        if after_changed != before_changed:
            raise RuntimeError("changed-file denial created a read ACTION")
        print("FILE_CHANGED_AFTER_SEARCH> BLOCKED")
        print("CHANGED_FILE_READ_ACTIONS> 0")

        # Registry revision drift must also fail before a read ACTION.
        registry.upsert_project(
            actor_kind="owner",
            owner_id="owner-run057",
            project_id="project-alpha",
            name="Alpha",
            trusted_root=alpha_root,
            trust_class=TrustClass.OWNER_PROJECT,
            repo_identity="https://example.invalid/project-alpha.git",
            archive_state=ArchiveState.ACTIVE,
            read_policy=ReadPolicy.ALLOWED,
            write_policy=WritePolicy.OWNER_APPROVAL,
            no_cloud=False,
            license_state="OWNER",
            revision="alpha-057-b",
        )
        before_stale = count_read_actions(
            store,
            state_project.project_id,
            task.task_id,
        )
        stale_blocked = False
        try:
            read_verified_workspace_text(
                store,
                registry,
                task_id=task.task_id,
                workspace_result_event_id=search.result_event_id,
                path_identity_sha256=alpha_target["path_identity_sha256"],
            )
        except OperatorControlDenied as exc:
            stale_blocked = exc.code == "workspace_evidence_stale"
        if not stale_blocked:
            raise RuntimeError("registry-stale evidence read was not blocked")
        after_stale = count_read_actions(
            store,
            state_project.project_id,
            task.task_id,
        )
        if after_stale != before_stale:
            raise RuntimeError("registry-stale denial created a read ACTION")
        print("REGISTRY_CHANGED_AFTER_SEARCH> BLOCKED")
        print("STALE_EVIDENCE_READ_ACTIONS> 0")

        # Validate read causal children for successful normal read.
        action_event = store.get_event(read.action_event_id)
        evidence_event = store.get_event(read.evidence_event_id)
        result_event = store.get_event(read.result_event_id)
        if action_event is None or evidence_event is None or result_event is None:
            raise RuntimeError("verified text read causal events missing")
        if action_event.parent_event_id != search.result_event_id:
            raise RuntimeError("verified text ACTION not parented to workspace RESULT")
        if evidence_event.parent_event_id != action_event.event_id:
            raise RuntimeError("verified text EVIDENCE not parented to read ACTION")
        if result_event.parent_event_id != evidence_event.event_id:
            raise RuntimeError("verified text RESULT not parented to read EVIDENCE")
        print("VERIFIED_TEXT_CAUSAL_CHAIN> PASS")

        summary = {
            "schema": "orion.v3.verified-workspace-text-read.v0",
            "run_id": "V3-RUN-058",
            "model_calls": 0,
            "external_provider_calls": 0,
            "prerequisite_real_workspace_hand_calls": 1,
            "model_path_arguments": 0,
            "model_evidence_identity_arguments": 1,
            "successful_content_reads": 2,
            "root_leak": False,
            "forged_identity_blocked": True,
            "file_changed_after_search_blocked": True,
            "registry_changed_after_search_blocked": True,
            "bounded_truncation_visible": True,
            "content_hash_verified": True,
        }
        print(
            "ORION_VERIFIED_TEXT_READ_SUMMARY> "
            + json.dumps(summary, ensure_ascii=False, sort_keys=True)
        )
        store.close()

    print("ORION_VERIFIED_TEXT_READ> PASS")
    print("STATUS> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
