from pathlib import Path

import hashlib
import pytest

from orion_v3.evidence import EvidenceEnvelope, Outcome

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


def deterministic_workspace_runner(task_id, exact_names, project_ids, trusted_roots):
    matches = []
    wanted = {name.casefold() for name in exact_names}
    for project_id in project_ids:
        root = Path(trusted_roots[project_id]).resolve()
        for entry in sorted(root.rglob("*"), key=lambda p: p.as_posix().casefold()):
            if not entry.is_file():
                continue
            if entry.name.casefold() not in wanted:
                continue
            stat = entry.stat()
            matches.append(
                {
                    "location": project_id,
                    "relative_path": entry.relative_to(root).as_posix(),
                    "name": entry.name,
                    "kind": "file",
                    "size_bytes": stat.st_size,
                    "modified_ns": stat.st_mtime_ns,
                }
            )
    return (
        EvidenceEnvelope(
            task_id=task_id,
            lease_id="lease-unit-workspace",
            operation_id="filesystem.search",
            implementation_id="openjarvis.tool.orion_filesystem_search.v1",
            outcome=Outcome.CONFIRMED,
            result={
                "operation_id": "filesystem.search",
                "implementation_id": "openjarvis.tool.orion_filesystem_search.v1",
                "searched_locations": list(project_ids),
                "matches": matches,
                "match_count": len(matches),
                "truncated": False,
            },
            verifier="orion.openjarvis.filesystem_search.v1",
        ),
        "lease-unit-workspace",
    )


def make_runtime(tmp_path: Path):
    store = OrionStateStore(tmp_path / "orion.db")
    store.initialize()
    project = store.create_project("Content", project_id="content-state")
    task = store.create_task(project.project_id, "Find and read target.txt", task_id="content-task")
    registry = WorkspaceRegistry(store)
    registry.initialize()

    roots = {}
    for project_id, name, revision in (
        ("p-a", "Alpha", "sha-a"),
        ("p-b", "Beta", "sha-b"),
    ):
        root = tmp_path / project_id
        root.mkdir()
        (root / "target.txt").write_bytes(
            b"alpha content\n" if project_id == "p-a" else b"beta content\n"
        )
        roots[project_id] = root
        registry.upsert_project(
            actor_kind="owner",
            owner_id="owner",
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
    proposal = propose_workspace_search(
        store,
        registry,
        task_id=task.task_id,
        exact_names=["target.txt"],
        scope_token="registered_projects",
        proposed_by="qwen35-9b-orion",
    )
    execution = execute_workspace_search(
        store,
        registry,
        task_id=task.task_id,
        proposal_event_id=proposal.event_id,
        search_runner=deterministic_workspace_runner,
    )
    return store, registry, task, roots, execution


def test_verified_text_tool_exposes_only_evidence_identity():
    tool = verified_text_read_tool_spec()
    fn = tool["function"]
    assert fn["name"] == "orion_read_verified_text"
    assert set(fn["parameters"]["properties"]) == {"path_identity_sha256"}
    assert fn["parameters"]["required"] == ["path_identity_sha256"]
    assert fn["parameters"]["additionalProperties"] is False


def test_verified_text_read_uses_exact_search_evidence_and_hides_root(tmp_path: Path):
    store, registry, task, roots, search = make_runtime(tmp_path)
    alpha = next(
        item for item in search.verified_result["matches"]
        if item["project_id"] == "p-a"
    )

    result = read_verified_workspace_text(
        store,
        registry,
        task_id=task.task_id,
        workspace_result_event_id=search.result_event_id,
        path_identity_sha256=alpha["path_identity_sha256"],
        max_bytes=1024,
    )

    assert result.project_id == "p-a"
    assert result.relative_path == "target.txt"
    assert result.text == "alpha content\n"
    assert result.truncated is False
    assert result.bytes_read == len(b"alpha content\n")
    assert result.content_sha256 == hashlib.sha256(b"alpha content\n").hexdigest()

    final = store.get_event(result.result_event_id)
    assert final is not None
    assert final.event_type == EventType.RESULT
    assert final.payload["kind"] == "verified_workspace_text_result"
    assert final.payload["authority"] == "verified_read_only_evidence"
    assert final.payload["absolute_root_exposed"] is False
    encoded = repr(final.payload)
    for root in roots.values():
        assert str(root.resolve()) not in encoded


def test_unknown_evidence_identity_is_denied_without_read_events(tmp_path: Path):
    store, registry, task, _, search = make_runtime(tmp_path)
    before = store.list_task_events(task.project_id, task.task_id)

    with pytest.raises(OperatorControlDenied) as exc:
        read_verified_workspace_text(
            store,
            registry,
            task_id=task.task_id,
            workspace_result_event_id=search.result_event_id,
            path_identity_sha256="0" * 64,
        )

    assert exc.value.code == "unknown_evidence_identity"
    after = store.list_task_events(task.project_id, task.task_id)
    assert [e.event_id for e in after] == [e.event_id for e in before]


def test_file_change_after_search_is_denied_before_action(tmp_path: Path):
    store, registry, task, roots, search = make_runtime(tmp_path)
    alpha = next(
        item for item in search.verified_result["matches"]
        if item["project_id"] == "p-a"
    )
    before = store.list_task_events(task.project_id, task.task_id)
    (roots["p-a"] / "target.txt").write_text("changed content with new length\n", encoding="utf-8")

    with pytest.raises(OperatorControlDenied) as exc:
        read_verified_workspace_text(
            store,
            registry,
            task_id=task.task_id,
            workspace_result_event_id=search.result_event_id,
            path_identity_sha256=alpha["path_identity_sha256"],
        )

    assert exc.value.code == "workspace_file_changed"
    after = store.list_task_events(task.project_id, task.task_id)
    assert [e.event_id for e in after] == [e.event_id for e in before]


def test_registry_change_after_search_is_denied_before_action(tmp_path: Path):
    store, registry, task, roots, search = make_runtime(tmp_path)
    beta = next(
        item for item in search.verified_result["matches"]
        if item["project_id"] == "p-b"
    )
    registry.upsert_project(
        actor_kind="owner",
        owner_id="owner",
        project_id="p-b",
        name="Beta",
        trusted_root=roots["p-b"],
        trust_class=TrustClass.OWNER_PROJECT,
        repo_identity="https://example.invalid/p-b.git",
        archive_state=ArchiveState.ACTIVE,
        read_policy=ReadPolicy.ALLOWED,
        write_policy=WritePolicy.OWNER_APPROVAL,
        no_cloud=False,
        license_state="OWNER",
        revision="sha-b-2",
    )
    before = store.list_task_events(task.project_id, task.task_id)

    with pytest.raises(OperatorControlDenied) as exc:
        read_verified_workspace_text(
            store,
            registry,
            task_id=task.task_id,
            workspace_result_event_id=search.result_event_id,
            path_identity_sha256=beta["path_identity_sha256"],
        )

    assert exc.value.code == "workspace_evidence_stale"
    after = store.list_task_events(task.project_id, task.task_id)
    assert [e.event_id for e in after] == [e.event_id for e in before]


def test_bounded_read_reports_truncation_explicitly(tmp_path: Path):
    store = OrionStateStore(tmp_path / "bounded.db")
    store.initialize()
    project = store.create_project("Bounded", project_id="bounded-state")
    task = store.create_task(project.project_id, "Read big.txt", task_id="bounded-task")
    registry = WorkspaceRegistry(store)
    registry.initialize()
    root = tmp_path / "bounded-project"
    root.mkdir()
    content = "x" * 200
    (root / "big.txt").write_text(content, encoding="utf-8")
    registry.upsert_project(
        actor_kind="owner",
        owner_id="owner",
        project_id="p-big",
        name="Big",
        trusted_root=root,
        trust_class=TrustClass.OWNER_PROJECT,
        repo_identity="https://example.invalid/p-big.git",
        archive_state=ArchiveState.ACTIVE,
        read_policy=ReadPolicy.ALLOWED,
        write_policy=WritePolicy.OWNER_APPROVAL,
        no_cloud=False,
        license_state="OWNER",
        revision="sha-big",
    )
    proposal = propose_workspace_search(
        store,
        registry,
        task_id=task.task_id,
        exact_names=["big.txt"],
        scope_token="registered_projects",
        proposed_by="qwen35-9b-orion",
    )
    search = execute_workspace_search(
        store,
        registry,
        task_id=task.task_id,
        proposal_event_id=proposal.event_id,
        search_runner=deterministic_workspace_runner,
    )
    item = search.verified_result["matches"][0]
    result = read_verified_workspace_text(
        store,
        registry,
        task_id=task.task_id,
        workspace_result_event_id=search.result_event_id,
        path_identity_sha256=item["path_identity_sha256"],
        max_bytes=64,
    )
    assert result.bytes_read == 64
    assert result.truncated is True
    assert result.text == "x" * 64
    assert result.content_sha256 == hashlib.sha256(b"x" * 64).hexdigest()
