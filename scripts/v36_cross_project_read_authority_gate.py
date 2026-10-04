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
    OperatorControlDenied,
    execute_workspace_search,
    propose_workspace_search,
)
from orion_v3.state import EventType, OrionStateStore
from orion_v3.workspaces import (
    ArchiveState,
    ReadPolicy,
    TrustClass,
    WorkspaceRegistry,
    WritePolicy,
)


TARGET = "__ORION_RUN055_SHARED_SOLUTION__.py"


def register_project(
    registry: WorkspaceRegistry,
    *,
    project_id: str,
    name: str,
    root: Path,
    revision: str,
    no_cloud: bool,
):
    return registry.upsert_project(
        actor_kind="owner",
        owner_id="owner-run055",
        project_id=project_id,
        name=name,
        trusted_root=root,
        trust_class=TrustClass.OWNER_PROJECT,
        repo_identity=f"https://example.invalid/{project_id}.git",
        archive_state=ArchiveState.ACTIVE,
        read_policy=ReadPolicy.ALLOWED,
        write_policy=WritePolicy.OWNER_APPROVAL,
        no_cloud=no_cloud,
        license_state="OWNER",
        revision=revision,
    )


def main() -> int:
    print("V3_RUN_ID> V3-RUN-055")
    print("ORION_CROSS_PROJECT_READ_AUTHORITY> START")
    print("MODE> frozen registry scope -> Action Lease -> real OpenJarvis Hand -> provenance")
    print("MODEL_CALLS> 0")
    print("EXTERNAL_PROVIDER_CALLS> 0")

    with tempfile.TemporaryDirectory(prefix="orion-run055-") as td:
        temp = Path(td)
        root_a = temp / "projects" / "alpha"
        root_b = temp / "projects" / "beta"
        root_a.mkdir(parents=True)
        root_b.mkdir(parents=True)

        (root_a / "src").mkdir()
        (root_b / "src").mkdir()
        (root_a / "src" / TARGET).write_text(
            "SOURCE='alpha'\n",
            encoding="utf-8",
        )
        (root_b / "src" / TARGET).write_text(
            "SOURCE='beta'\n",
            encoding="utf-8",
        )

        db = temp / "orion.db"
        store = OrionStateStore(db)
        store.initialize()
        state_project = store.create_project(
            "RUN-055 authority task",
            project_id="run055-state-project",
        )
        task = store.create_task(
            state_project.project_id,
            "Find the shared solution file across my registered projects.",
            task_id="run055-task",
        )

        registry = WorkspaceRegistry(store)
        registry.initialize()
        register_project(
            registry,
            project_id="project-alpha",
            name="Alpha Project",
            root=root_a,
            revision="alpha-sha-001",
            no_cloud=False,
        )
        register_project(
            registry,
            project_id="project-beta",
            name="Beta Project",
            root=root_b,
            revision="beta-sha-002",
            no_cloud=True,
        )
        print("REGISTERED_PROJECT_FIXTURE> PASS 2")

        proposal = propose_workspace_search(
            store,
            registry,
            task_id=task.task_id,
            exact_names=[TARGET],
            scope_token="registered_projects",
            proposed_by="deterministic-run055",
            max_projects=4,
        )
        if proposal.project_ids != ("project-alpha", "project-beta"):
            raise RuntimeError("frozen project set mismatch")
        print("FROZEN_SCOPE_PROJECT_SET> PASS")
        print("FROZEN_SCOPE_RESOLUTION_ID> " + proposal.resolution_id)

        proposal_event = store.get_event(proposal.event_id)
        if proposal_event is None:
            raise RuntimeError("workspace proposal missing")
        proposal_encoded = json.dumps(
            proposal_event.payload,
            ensure_ascii=False,
            sort_keys=True,
        )
        if str(root_a.resolve()) in proposal_encoded or str(root_b.resolve()) in proposal_encoded:
            raise RuntimeError("absolute trusted root leaked into canonical workspace proposal")
        if "trusted_root" in proposal_encoded:
            raise RuntimeError("trusted_root field leaked into canonical workspace proposal")
        print("PROPOSAL_TRUSTED_ROOT_LEAK> 0")

        execution = execute_workspace_search(
            store,
            registry,
            task_id=task.task_id,
            proposal_event_id=proposal.event_id,
        )
        verified = execution.verified_result
        if verified.get("status") != "PASS":
            raise RuntimeError("workspace verified RESULT did not pass")
        if verified.get("project_ids") != ["project-alpha", "project-beta"]:
            raise RuntimeError("workspace Hand did not search exact frozen project set")
        if verified.get("searched_project_count") != 2:
            raise RuntimeError("workspace searched project count mismatch")
        if verified.get("match_count") != 2:
            raise RuntimeError("expected one same-path match in each project")
        if verified.get("found_names") != [TARGET]:
            raise RuntimeError("workspace found-name evidence mismatch")
        print("REAL_CROSS_PROJECT_HAND_SEARCH> PASS")
        print("SEARCHED_PROJECT_COUNT> 2")
        print("MATCH_COUNT> 2")

        matches = verified["matches"]
        if [item["project_id"] for item in matches] != [
            "project-alpha",
            "project-beta",
        ]:
            raise RuntimeError("cross-project provenance order/identity mismatch")
        if not all(item["relative_path"] == f"src/{TARGET}" for item in matches):
            raise RuntimeError("same-relative-path physical fixture mismatch")
        if matches[0]["path_identity_sha256"] == matches[1]["path_identity_sha256"]:
            raise RuntimeError("same relative path collided across project provenance")
        print("SAME_RELATIVE_PATH_PROVENANCE_DISTINCT> PASS")

        alpha, beta = matches
        if alpha["project_name"] != "Alpha Project":
            raise RuntimeError("alpha human project provenance missing")
        if alpha["repo_identity"] != "https://example.invalid/project-alpha.git":
            raise RuntimeError("alpha repo provenance missing")
        if alpha["revision"] != "alpha-sha-001":
            raise RuntimeError("alpha revision provenance missing")
        if alpha["trust_class"] != "owner_project":
            raise RuntimeError("alpha trust provenance missing")
        if alpha["license_state"] != "OWNER":
            raise RuntimeError("alpha license provenance missing")
        if alpha["no_cloud"] is not False:
            raise RuntimeError("alpha no_cloud provenance mismatch")
        if beta["no_cloud"] is not True:
            raise RuntimeError("beta no_cloud provenance missing")
        print("PROJECT_PROVENANCE_FIELDS> PASS")
        print("NO_CLOUD_PROVENANCE> PASS")

        verified_encoded = json.dumps(verified, ensure_ascii=False, sort_keys=True)
        if str(root_a.resolve()) in verified_encoded or str(root_b.resolve()) in verified_encoded:
            raise RuntimeError("absolute trusted root leaked into verified workspace RESULT")
        if "trusted_root" in verified_encoded:
            raise RuntimeError("trusted_root field leaked into verified workspace RESULT")
        print("RESULT_TRUSTED_ROOT_LEAK> 0")

        events = store.list_task_events(state_project.project_id, task.task_id)
        if [event.event_type for event in events] != [
            EventType.PROPOSAL,
            EventType.ACTION,
            EventType.EVIDENCE,
            EventType.RESULT,
        ]:
            raise RuntimeError("unexpected cross-project canonical event chain")
        if events[1].parent_event_id != events[0].event_id:
            raise RuntimeError("ACTION not parented to workspace PROPOSAL")
        if events[2].parent_event_id != events[1].event_id:
            raise RuntimeError("EVIDENCE not parented to ACTION")
        if events[3].parent_event_id != events[2].event_id:
            raise RuntimeError("RESULT not parented to EVIDENCE")
        print("CROSS_PROJECT_CAUSAL_CHAIN> PASS")

        duplicate_blocked = False
        try:
            execute_workspace_search(
                store,
                registry,
                task_id=task.task_id,
                proposal_event_id=proposal.event_id,
            )
        except OperatorControlDenied as exc:
            duplicate_blocked = exc.code == "proposal_already_dispatched"
        if not duplicate_blocked:
            raise RuntimeError("workspace proposal replay was not blocked")
        print("DUPLICATE_WORKSPACE_DISPATCH> BLOCKED")

        stale_task = store.create_task(
            state_project.project_id,
            "Prove registry change invalidates a frozen workspace proposal.",
            task_id="run055-stale-task",
        )
        stale_proposal = propose_workspace_search(
            store,
            registry,
            task_id=stale_task.task_id,
            exact_names=[TARGET],
            scope_token="registered_projects",
            proposed_by="deterministic-run055",
            max_projects=4,
        )
        registry.upsert_project(
            actor_kind="owner",
            owner_id="owner-run055",
            project_id="project-beta",
            name="Beta Project",
            trusted_root=root_b,
            trust_class=TrustClass.OWNER_PROJECT,
            repo_identity="https://example.invalid/project-beta.git",
            archive_state=ArchiveState.ACTIVE,
            read_policy=ReadPolicy.ALLOWED,
            write_policy=WritePolicy.OWNER_APPROVAL,
            no_cloud=True,
            license_state="OWNER",
            revision="beta-sha-003",
        )

        stale_blocked = False
        try:
            execute_workspace_search(
                store,
                registry,
                task_id=stale_task.task_id,
                proposal_event_id=stale_proposal.event_id,
            )
        except OperatorControlDenied as exc:
            stale_blocked = exc.code == "workspace_scope_stale"
        if not stale_blocked:
            raise RuntimeError("registry revision change did not invalidate frozen proposal")
        stale_events = store.list_task_events(
            state_project.project_id,
            stale_task.task_id,
        )
        if [event.event_type for event in stale_events] != [EventType.PROPOSAL]:
            raise RuntimeError("stale workspace proposal reached ACTION/Hand")
        print("REGISTRY_CHANGE_AFTER_FREEZE> BLOCKED")
        print("STALE_PROPOSAL_HAND_EXECUTIONS> 0")

        summary = {
            "schema": "orion.v3.cross-project-read-authority.v0",
            "run_id": "V3-RUN-055",
            "capability_id": "workspace.search_exact",
            "semantic_scope": "registered_projects",
            "project_ids": ["project-alpha", "project-beta"],
            "real_hand": "openjarvis.tool.orion_filesystem_search.v1",
            "searched_project_count": 2,
            "match_count": 2,
            "same_relative_path_provenance_distinct": True,
            "trusted_root_leak": False,
            "duplicate_dispatch_blocked": True,
            "registry_change_after_freeze_blocked": True,
            "stale_proposal_hand_executions": 0,
            "model_calls": 0,
            "external_provider_calls": 0,
        }
        print(
            "ORION_CROSS_PROJECT_READ_SUMMARY> "
            + json.dumps(summary, ensure_ascii=False, sort_keys=True)
        )
        store.close()

    print("ORION_CROSS_PROJECT_READ_AUTHORITY> PASS")
    print("STATUS> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
