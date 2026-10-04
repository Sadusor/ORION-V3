from __future__ import annotations

import json
import tempfile
from pathlib import Path

from orion_v3.state import OrionStateStore
from orion_v3.workspaces import (
    ArchiveState,
    ReadPolicy,
    RegistryDenied,
    TrustClass,
    WorkspaceRegistry,
    WritePolicy,
)


def main() -> int:
    print("V3_RUN_ID> V3-RUN-054")
    print("ORION_WORKSPACE_REGISTRY> START")
    print("MODE> deterministic registry foundation; zero model; zero network; zero Hand")

    with tempfile.TemporaryDirectory(prefix="orion-run054-") as td:
        root = Path(td)
        db = root / "orion.db"
        store = OrionStateStore(db)
        store.initialize()
        registry = WorkspaceRegistry(store)
        registry.initialize()

        roots = {
            "active": root / "roots" / "active",
            "other": root / "roots" / "other",
            "client": root / "roots" / "client",
            "donor": root / "roots" / "donor",
            "archived": root / "roots" / "archived",
        }
        for path in roots.values():
            path.mkdir(parents=True, exist_ok=True)

        active = registry.upsert_project(
            actor_kind="owner",
            owner_id="owner-run054",
            project_id="project-active",
            name="Active Project",
            trusted_root=roots["active"],
            trust_class=TrustClass.OWNER_PROJECT,
            repo_identity="https://example.invalid/owner/active.git",
            archive_state=ArchiveState.ACTIVE,
            read_policy=ReadPolicy.ALLOWED,
            write_policy=WritePolicy.OWNER_APPROVAL,
            no_cloud=False,
            license_state="OWNER",
            revision="active-sha-1",
        )
        other = registry.upsert_project(
            actor_kind="owner",
            owner_id="owner-run054",
            project_id="project-other",
            name="Other Project",
            trusted_root=roots["other"],
            trust_class=TrustClass.OWNER_PROJECT,
            repo_identity="https://example.invalid/owner/other.git",
            archive_state=ArchiveState.ACTIVE,
            read_policy=ReadPolicy.ALLOWED,
            write_policy=WritePolicy.OWNER_APPROVAL,
            no_cloud=False,
            license_state="OWNER",
            revision="other-sha-1",
        )
        client = registry.upsert_project(
            actor_kind="owner",
            owner_id="owner-run054",
            project_id="project-client",
            name="Client Project",
            trusted_root=roots["client"],
            trust_class=TrustClass.SHARED_OR_CLIENT,
            repo_identity="https://example.invalid/client/private.git",
            archive_state=ArchiveState.ACTIVE,
            read_policy=ReadPolicy.ALLOWED,
            write_policy=WritePolicy.OWNER_APPROVAL,
            no_cloud=True,
            license_state="PRIVATE",
            revision="client-sha-1",
        )
        donor = registry.upsert_project(
            actor_kind="owner",
            owner_id="owner-run054",
            project_id="project-donor",
            name="Open Donor",
            trusted_root=roots["donor"],
            trust_class=TrustClass.DONOR_REPO,
            repo_identity="https://github.com/example/open-donor",
            archive_state=ArchiveState.ACTIVE,
            read_policy=ReadPolicy.ALLOWED,
            write_policy=WritePolicy.DENY,
            no_cloud=False,
            license_state="Apache-2.0",
            revision="donor-sha-1",
        )
        archived = registry.upsert_project(
            actor_kind="owner",
            owner_id="owner-run054",
            project_id="project-archived",
            name="Archived Project",
            trusted_root=roots["archived"],
            trust_class=TrustClass.OWNER_PROJECT,
            repo_identity="https://example.invalid/owner/archived.git",
            archive_state=ArchiveState.ARCHIVED,
            read_policy=ReadPolicy.ALLOWED,
            write_policy=WritePolicy.OWNER_APPROVAL,
            no_cloud=False,
            license_state="OWNER",
            revision="archived-sha-1",
        )
        print("REGISTRY_PROJECT_CREATION> PASS")
        print("REGISTRY_VERSIONING_INITIAL> PASS")

        if any(item.version != 1 for item in (active, other, client, donor, archived)):
            raise RuntimeError("initial registry versions were not 1")
        if len({item.record_sha256 for item in (active, other, client, donor, archived)}) != 5:
            raise RuntimeError("registry checksums unexpectedly collided")

        model_mutation_blocked = False
        try:
            registry.upsert_project(
                actor_kind="local_model",
                owner_id="qwen35-9b-orion",
                project_id="project-model-created",
                name="Model Created",
                trusted_root=root / "roots" / "model-created",
                trust_class=TrustClass.OWNER_PROJECT,
            )
        except RegistryDenied as exc:
            model_mutation_blocked = exc.code == "registry_owner_only"
        if not model_mutation_blocked:
            raise RuntimeError("model registry mutation was not blocked")
        print("MODEL_REGISTRY_MUTATION> BLOCKED")

        group = registry.upsert_group(
            actor_kind="owner",
            owner_id="owner-run054",
            group_id="work",
            name="Work Projects",
            member_project_ids=[
                "project-active",
                "project-other",
                "project-client",
            ],
        )
        if group.version != 1:
            raise RuntimeError("initial group version mismatch")
        print("OWNER_GROUP_CREATION> PASS")

        group_mutation_blocked = False
        try:
            registry.upsert_group(
                actor_kind="local_model",
                owner_id="qwen35-9b-orion",
                group_id="work",
                name="Work Projects",
                member_project_ids=["project-donor"],
            )
        except RegistryDenied as exc:
            group_mutation_blocked = exc.code == "registry_owner_only"
        if not group_mutation_blocked:
            raise RuntimeError("model group-membership mutation was not blocked")
        print("MODEL_GROUP_MEMBERSHIP_MUTATION> BLOCKED")

        active_scope = registry.resolve_scope(
            "active_project",
            active_project_id="project-active",
        )
        if [p.project_id for p in active_scope.projects] != ["project-active"]:
            raise RuntimeError("active_project resolution mismatch")
        print("SCOPE_ACTIVE_PROJECT> PASS")

        registered = registry.resolve_scope("registered_projects")
        registered_ids = [p.project_id for p in registered.projects]
        if registered_ids != [
            "project-active",
            "project-client",
            "project-other",
        ]:
            raise RuntimeError("registered_projects resolution mismatch: " + repr(registered_ids))
        print("SCOPE_REGISTERED_PROJECTS> PASS")

        donors = registry.resolve_scope("donor_repos")
        if [p.project_id for p in donors.projects] != ["project-donor"]:
            raise RuntimeError("donor scope resolution mismatch")
        if donors.projects[0].license_state != "Apache-2.0":
            raise RuntimeError("donor license provenance missing")
        print("SCOPE_DONOR_REPOS> PASS")
        print("DONOR_LICENSE_METADATA> PASS")

        archived_scope = registry.resolve_scope("archived_projects")
        if [p.project_id for p in archived_scope.projects] != ["project-archived"]:
            raise RuntimeError("archived scope resolution mismatch")
        print("SCOPE_ARCHIVED_PROJECTS_EXPLICIT> PASS")

        archived_default_blocked = False
        try:
            registry.resolve_scope(
                "active_project",
                active_project_id="project-archived",
            )
        except RegistryDenied as exc:
            archived_default_blocked = exc.code == "archived_project_not_explicit"
        if not archived_default_blocked:
            raise RuntimeError("archived project was not default-excluded")
        print("ARCHIVED_DEFAULT_EXCLUSION> PASS")

        group_scope = registry.resolve_scope("project_group:work")
        if [p.project_id for p in group_scope.projects] != [
            "project-active",
            "project-other",
            "project-client",
        ]:
            raise RuntimeError("group scope resolution mismatch")
        print("SCOPE_OWNER_GROUP> PASS")

        safe_packet = registered.model_safe()
        encoded_safe = json.dumps(safe_packet, ensure_ascii=False, sort_keys=True)
        for path in roots.values():
            if str(path.resolve()) in encoded_safe:
                raise RuntimeError("trusted absolute root leaked into model-safe scope packet")
        if "trusted_root" in encoded_safe:
            raise RuntimeError("trusted_root field leaked into model-safe scope packet")
        if not any(p["no_cloud"] is True for p in safe_packet["projects"]):
            raise RuntimeError("no_cloud policy metadata missing from model-safe scope packet")
        print("MODEL_SAFE_SCOPE_PACKET> PASS")
        print("TRUSTED_ROOT_LEAK> 0")
        print("NO_CLOUD_METADATA_VISIBLE> PASS")

        cap_blocked = False
        try:
            registry.resolve_scope("registered_projects", max_projects=2)
        except RegistryDenied as exc:
            cap_blocked = exc.code == "scope_project_cap_exceeded"
        if not cap_blocked:
            raise RuntimeError("scope project-count cap was not enforced")
        print("SCOPE_PROJECT_CAP> BLOCKED")

        frozen = registry.resolve_scope("registered_projects")
        frozen_packet = frozen.model_safe()
        frozen_id = frozen.resolution_id
        frozen_other = next(p for p in frozen.projects if p.project_id == "project-other")

        other_v2 = registry.upsert_project(
            actor_kind="owner",
            owner_id="owner-run054",
            project_id="project-other",
            name="Other Project",
            trusted_root=roots["other"],
            trust_class=TrustClass.OWNER_PROJECT,
            repo_identity="https://example.invalid/owner/other.git",
            archive_state=ArchiveState.ACTIVE,
            read_policy=ReadPolicy.ALLOWED,
            write_policy=WritePolicy.OWNER_APPROVAL,
            no_cloud=True,
            license_state="OWNER",
            revision="other-sha-2",
        )
        if other_v2.version != 2:
            raise RuntimeError("project registry version did not increment")
        current = registry.resolve_scope("registered_projects")
        current_other = next(p for p in current.projects if p.project_id == "project-other")
        if frozen.resolution_id != frozen_id or frozen.model_safe() != frozen_packet:
            raise RuntimeError("previously resolved scope silently changed")
        if current.resolution_id == frozen_id:
            raise RuntimeError("new resolution did not reflect registry revision")
        if frozen_other.registry_version != 1 or current_other.registry_version != 2:
            raise RuntimeError("scope did not preserve exact registry versions")
        if frozen_other.revision != "other-sha-1" or current_other.revision != "other-sha-2":
            raise RuntimeError("scope did not preserve exact repo revisions")
        print("FROZEN_SCOPE_STABILITY> PASS")
        print("NEW_RESOLUTION_AFTER_REGISTRY_CHANGE> PASS")

        # Direct current-row tamper must be caught against immutable revision.
        store.connect().execute(
            """
            UPDATE workspace_registry_projects
            SET trusted_root=?
            WHERE project_id='project-client'
            """,
            (str((root / "roots" / "tampered-client").resolve()),),
        )
        store.connect().commit()
        integrity_blocked = False
        try:
            registry.resolve_scope("project:project-client")
        except RegistryDenied as exc:
            integrity_blocked = exc.code == "registry_integrity_failure"
        if not integrity_blocked:
            raise RuntimeError("direct project-root tamper was not detected")
        print("DIRECT_REGISTRY_ROOT_TAMPER> BLOCKED")

        # Group current-row tamper must also be caught against immutable revision.
        store.connect().execute(
            """
            UPDATE workspace_registry_groups
            SET member_project_ids_json='["project-donor"]'
            WHERE group_id='work'
            """
        )
        store.connect().commit()
        group_integrity_blocked = False
        try:
            registry.resolve_scope("project_group:work")
        except RegistryDenied as exc:
            group_integrity_blocked = exc.code == "registry_integrity_failure"
        if not group_integrity_blocked:
            raise RuntimeError("direct group-membership tamper was not detected")
        print("DIRECT_GROUP_MEMBERSHIP_TAMPER> BLOCKED")

        summary = {
            "schema": "orion.v3.workspace-registry-foundation.v0",
            "run_id": "V3-RUN-054",
            "projects_registered": 5,
            "owner_groups": 1,
            "model_registry_mutations_allowed": 0,
            "model_group_mutations_allowed": 0,
            "semantic_scopes_proven": [
                "active_project",
                "registered_projects",
                "donor_repos",
                "archived_projects",
                "project_group:work",
            ],
            "trusted_root_leak": False,
            "scope_cap_enforced": True,
            "frozen_scope_stable_after_registry_change": True,
            "new_resolution_changes_after_registry_revision": True,
            "direct_root_tamper_blocked": True,
            "direct_group_tamper_blocked": True,
            "external_provider_calls": 0,
            "hand_executions": 0,
            "model_calls": 0,
        }
        print(
            "ORION_WORKSPACE_REGISTRY_SUMMARY> "
            + json.dumps(summary, ensure_ascii=False, sort_keys=True)
        )
        store.close()

    print("ORION_WORKSPACE_REGISTRY> PASS")
    print("STATUS> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
