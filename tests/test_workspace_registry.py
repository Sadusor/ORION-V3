from pathlib import Path

import pytest

from orion_v3.state import OrionStateStore
from orion_v3.workspaces import (
    ArchiveState,
    ReadPolicy,
    RegistryDenied,
    TrustClass,
    WorkspaceRegistry,
    WritePolicy,
)


def make_registry(tmp_path: Path):
    store = OrionStateStore(tmp_path / "orion.db")
    store.initialize()
    registry = WorkspaceRegistry(store)
    registry.initialize()
    return store, registry


def add_project(
    registry: WorkspaceRegistry,
    *,
    project_id: str,
    name: str,
    root: Path,
    trust: TrustClass = TrustClass.OWNER_PROJECT,
    archived: bool = False,
    read: ReadPolicy = ReadPolicy.ALLOWED,
    no_cloud: bool = False,
    license_state: str = "OWNER",
    revision: str | None = None,
):
    root.mkdir(parents=True, exist_ok=True)
    return registry.upsert_project(
        actor_kind="owner",
        owner_id="owner-test",
        project_id=project_id,
        name=name,
        trusted_root=root,
        trust_class=trust,
        repo_identity=f"https://example.invalid/{project_id}.git",
        archive_state=(
            ArchiveState.ARCHIVED if archived else ArchiveState.ACTIVE
        ),
        read_policy=read,
        write_policy=WritePolicy.OWNER_APPROVAL,
        no_cloud=no_cloud,
        license_state=license_state,
        revision=revision,
    )


def test_registry_mutation_is_owner_only(tmp_path: Path):
    _, registry = make_registry(tmp_path)

    with pytest.raises(RegistryDenied) as exc:
        registry.upsert_project(
            actor_kind="local_model",
            owner_id="qwen",
            project_id="p1",
            name="P1",
            trusted_root=tmp_path / "p1",
            trust_class=TrustClass.OWNER_PROJECT,
        )

    assert exc.value.code == "registry_owner_only"


def test_project_revisions_are_versioned_checksummed_and_append_only(tmp_path: Path):
    store, registry = make_registry(tmp_path)
    p1 = add_project(
        registry,
        project_id="p1",
        name="Project One",
        root=tmp_path / "p1",
        revision="sha-one",
    )
    p2 = registry.upsert_project(
        actor_kind="owner",
        owner_id="owner-test",
        project_id="p1",
        name="Project One",
        trusted_root=tmp_path / "p1",
        trust_class=TrustClass.OWNER_PROJECT,
        repo_identity="https://example.invalid/p1.git",
        archive_state=ArchiveState.ACTIVE,
        read_policy=ReadPolicy.ALLOWED,
        write_policy=WritePolicy.OWNER_APPROVAL,
        no_cloud=True,
        license_state="OWNER",
        revision="sha-two",
    )

    assert p1.version == 1
    assert p2.version == 2
    assert p1.record_sha256 != p2.record_sha256
    assert p1.revision_id != p2.revision_id

    rows = store.connect().execute(
        """
        SELECT * FROM workspace_registry_project_revisions
        WHERE project_id='p1'
        ORDER BY version
        """
    ).fetchall()
    assert len(rows) == 2
    assert rows[0]["record_sha256"] == p1.record_sha256
    assert rows[1]["record_sha256"] == p2.record_sha256

    with pytest.raises(Exception):
        store.connect().execute(
            """
            UPDATE workspace_registry_project_revisions
            SET record_sha256='tampered'
            WHERE revision_id=?
            """,
            (p1.revision_id,),
        )


def test_model_safe_scope_hides_trusted_roots(tmp_path: Path):
    _, registry = make_registry(tmp_path)
    root_a = tmp_path / "secret-a"
    root_b = tmp_path / "secret-b"
    add_project(
        registry,
        project_id="a",
        name="Alpha",
        root=root_a,
        revision="aaa111",
    )
    add_project(
        registry,
        project_id="b",
        name="Beta",
        root=root_b,
        revision="bbb222",
        no_cloud=True,
    )

    resolution = registry.resolve_scope("registered_projects")
    packet = resolution.model_safe()
    encoded = repr(packet)

    assert packet["project_count"] == 2
    assert [p["project_id"] for p in packet["projects"]] == ["a", "b"]
    assert str(root_a.resolve()) not in encoded
    assert str(root_b.resolve()) not in encoded
    assert "trusted_root" not in encoded
    assert resolution.trusted_roots["a"] == str(root_a.resolve())
    assert resolution.trusted_roots["b"] == str(root_b.resolve())


def test_semantic_scopes_separate_owner_donor_and_archived(tmp_path: Path):
    _, registry = make_registry(tmp_path)
    add_project(
        registry,
        project_id="owner-a",
        name="Owner A",
        root=tmp_path / "owner-a",
    )
    add_project(
        registry,
        project_id="client-b",
        name="Client B",
        root=tmp_path / "client-b",
        trust=TrustClass.SHARED_OR_CLIENT,
        no_cloud=True,
    )
    add_project(
        registry,
        project_id="donor-c",
        name="Donor C",
        root=tmp_path / "donor-c",
        trust=TrustClass.DONOR_REPO,
        license_state="Apache-2.0",
    )
    add_project(
        registry,
        project_id="archived-d",
        name="Archived D",
        root=tmp_path / "archived-d",
        archived=True,
    )

    assert [
        p.project_id
        for p in registry.resolve_scope("registered_projects").projects
    ] == ["client-b", "owner-a"]
    assert [
        p.project_id
        for p in registry.resolve_scope("donor_repos").projects
    ] == ["donor-c"]
    assert [
        p.project_id
        for p in registry.resolve_scope("archived_projects").projects
    ] == ["archived-d"]

    with pytest.raises(RegistryDenied) as exc:
        registry.resolve_scope(
            "active_project",
            active_project_id="archived-d",
        )
    assert exc.value.code == "archived_project_not_explicit"


def test_owner_groups_are_versioned_and_model_cannot_mutate(tmp_path: Path):
    _, registry = make_registry(tmp_path)
    for project_id in ("a", "b", "c"):
        add_project(
            registry,
            project_id=project_id,
            name=project_id.upper(),
            root=tmp_path / project_id,
        )

    first = registry.upsert_group(
        actor_kind="owner",
        owner_id="owner-test",
        group_id="work",
        name="Work",
        member_project_ids=["a", "b"],
    )
    assert first.version == 1

    resolution = registry.resolve_scope("project_group:work")
    assert [p.project_id for p in resolution.projects] == ["a", "b"]

    second = registry.upsert_group(
        actor_kind="owner",
        owner_id="owner-test",
        group_id="work",
        name="Work",
        member_project_ids=["a", "b", "c"],
    )
    assert second.version == 2
    assert second.record_sha256 != first.record_sha256

    with pytest.raises(RegistryDenied) as exc:
        registry.upsert_group(
            actor_kind="local_model",
            owner_id="qwen",
            group_id="work",
            name="Work",
            member_project_ids=["a"],
        )
    assert exc.value.code == "registry_owner_only"


def test_scope_resolution_is_frozen_against_later_registry_change(tmp_path: Path):
    _, registry = make_registry(tmp_path)
    add_project(
        registry,
        project_id="a",
        name="Alpha",
        root=tmp_path / "a",
        revision="sha-a-1",
    )
    add_project(
        registry,
        project_id="b",
        name="Beta",
        root=tmp_path / "b",
        revision="sha-b-1",
    )

    frozen = registry.resolve_scope("registered_projects")
    frozen_packet = frozen.model_safe()
    frozen_id = frozen.resolution_id

    registry.upsert_project(
        actor_kind="owner",
        owner_id="owner-test",
        project_id="b",
        name="Beta",
        trusted_root=tmp_path / "b",
        trust_class=TrustClass.OWNER_PROJECT,
        repo_identity="https://example.invalid/b.git",
        archive_state=ArchiveState.ACTIVE,
        read_policy=ReadPolicy.ALLOWED,
        write_policy=WritePolicy.OWNER_APPROVAL,
        no_cloud=True,
        license_state="OWNER",
        revision="sha-b-2",
    )

    current = registry.resolve_scope("registered_projects")

    assert frozen.resolution_id == frozen_id
    assert frozen.model_safe() == frozen_packet
    assert current.resolution_id != frozen_id

    frozen_b = next(p for p in frozen.projects if p.project_id == "b")
    current_b = next(p for p in current.projects if p.project_id == "b")
    assert frozen_b.registry_version == 1
    assert current_b.registry_version == 2
    assert frozen_b.revision == "sha-b-1"
    assert current_b.revision == "sha-b-2"


def test_scope_caps_and_empty_scope_fail_closed(tmp_path: Path):
    _, registry = make_registry(tmp_path)
    add_project(
        registry,
        project_id="a",
        name="Alpha",
        root=tmp_path / "a",
    )
    add_project(
        registry,
        project_id="b",
        name="Beta",
        root=tmp_path / "b",
    )

    with pytest.raises(RegistryDenied) as exc:
        registry.resolve_scope("registered_projects", max_projects=1)
    assert exc.value.code == "scope_project_cap_exceeded"

    empty_store = OrionStateStore(tmp_path / "empty.db")
    empty_store.initialize()
    empty_registry = WorkspaceRegistry(empty_store)
    empty_registry.initialize()
    with pytest.raises(RegistryDenied) as exc:
        empty_registry.resolve_scope("registered_projects")
    assert exc.value.code == "empty_scope"
