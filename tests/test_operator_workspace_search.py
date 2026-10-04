from pathlib import Path

import pytest

from orion_v3.evidence import EvidenceEnvelope, Outcome
from orion_v3.operator import (
    OperatorControlDenied,
    execute_workspace_search,
    propose_workspace_search,
    workspace_search_tool_spec,
)
from orion_v3.state import EventType, OrionStateStore
from orion_v3.workspaces import (
    ArchiveState,
    ReadPolicy,
    TrustClass,
    WorkspaceRegistry,
    WritePolicy,
)


def make_runtime(tmp_path: Path):
    store = OrionStateStore(tmp_path / "orion.db")
    store.initialize()
    project = store.create_project("Active", project_id="task-project")
    task = store.create_task(
        project.project_id,
        "Search workspaces",
        task_id="workspace-task",
    )
    registry = WorkspaceRegistry(store)
    registry.initialize()

    roots = {}
    for project_id, name, revision in (
        ("p-a", "Alpha", "sha-a"),
        ("p-b", "Beta", "sha-b"),
    ):
        root = tmp_path / project_id
        root.mkdir()
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
            no_cloud=(project_id == "p-b"),
            license_state="OWNER",
            revision=revision,
        )
    return store, registry, task, roots


def confirmed_runner(task_id, exact_names, project_ids, trusted_roots):
    assert exact_names == ["target.py"]
    assert project_ids == ["p-a", "p-b"]
    assert set(trusted_roots) == {"p-a", "p-b"}
    return (
        EvidenceEnvelope(
            task_id=task_id,
            lease_id="lease-workspace",
            operation_id="filesystem.search",
            implementation_id="openjarvis.tool.orion_filesystem_search.v1",
            outcome=Outcome.CONFIRMED,
            result={
                "operation_id": "filesystem.search",
                "implementation_id": "openjarvis.tool.orion_filesystem_search.v1",
                "searched_locations": ["p-a", "p-b"],
                "matches": [
                    {
                        "location": "p-a",
                        "relative_path": "src/target.py",
                        "name": "target.py",
                        "kind": "file",
                        "size_bytes": 10,
                        "modified_ns": 1,
                    },
                    {
                        "location": "p-b",
                        "relative_path": "lib/target.py",
                        "name": "target.py",
                        "kind": "file",
                        "size_bytes": 20,
                        "modified_ns": 2,
                    },
                ],
                "match_count": 2,
                "truncated": False,
            },
            verifier="orion.openjarvis.filesystem_search.v1",
        ),
        "lease-workspace",
    )


def test_workspace_search_tool_exposes_semantics_only():
    tool = workspace_search_tool_spec(
        allowed_scope_tokens=[
            "active_project",
            "registered_projects",
            "project_group:work",
        ]
    )
    fn = tool["function"]
    assert fn["name"] == "orion_workspace_search_exact"
    assert set(fn["parameters"]["properties"]) == {
        "exact_names",
        "scope_token",
    }
    assert fn["parameters"]["properties"]["scope_token"]["enum"] == [
        "active_project",
        "project_group:work",
        "registered_projects",
    ]
    assert fn["parameters"]["additionalProperties"] is False


def test_workspace_proposal_freezes_registry_resolution_without_roots(tmp_path: Path):
    store, registry, task, roots = make_runtime(tmp_path)

    proposal = propose_workspace_search(
        store,
        registry,
        task_id=task.task_id,
        exact_names=["target.py"],
        scope_token="registered_projects",
        proposed_by="qwen35-9b-orion",
    )

    assert proposal.project_ids == ("p-a", "p-b")
    event = store.get_event(proposal.event_id)
    assert event is not None
    action = event.payload["action"]
    assert action["scope_token"] == "registered_projects"
    assert [item["project_id"] for item in action["projects"]] == ["p-a", "p-b"]
    encoded = repr(event.payload)
    for root in roots.values():
        assert str(root.resolve()) not in encoded
    assert "trusted_root" not in encoded


def test_workspace_execution_enriches_project_provenance_and_hides_roots(tmp_path: Path):
    store, registry, task, roots = make_runtime(tmp_path)
    proposal = propose_workspace_search(
        store,
        registry,
        task_id=task.task_id,
        exact_names=["target.py"],
        scope_token="registered_projects",
        proposed_by="qwen35-9b-orion",
    )

    execution = execute_workspace_search(
        store,
        registry,
        task_id=task.task_id,
        proposal_event_id=proposal.event_id,
        search_runner=confirmed_runner,
    )

    verified = execution.verified_result
    assert verified["status"] == "PASS"
    assert verified["project_ids"] == ["p-a", "p-b"]
    assert verified["searched_project_count"] == 2
    assert verified["match_count"] == 2
    assert verified["absolute_roots_exposed"] is False

    first, second = verified["matches"]
    assert first["project_id"] == "p-a"
    assert first["project_name"] == "Alpha"
    assert first["repo_identity"] == "https://example.invalid/p-a.git"
    assert first["revision"] == "sha-a"
    assert first["relative_path"] == "src/target.py"
    assert first["trust_class"] == "owner_project"
    assert first["license_state"] == "OWNER"
    assert first["no_cloud"] is False
    assert len(first["path_identity_sha256"]) == 64

    assert second["project_id"] == "p-b"
    assert second["project_name"] == "Beta"
    assert second["no_cloud"] is True

    encoded = repr(verified)
    for root in roots.values():
        assert str(root.resolve()) not in encoded

    events = store.list_task_events(task.project_id, task.task_id)
    assert [event.event_type for event in events] == [
        EventType.PROPOSAL,
        EventType.ACTION,
        EventType.EVIDENCE,
        EventType.RESULT,
    ]


def test_workspace_execution_rejects_registry_change_after_freeze(tmp_path: Path):
    store, registry, task, roots = make_runtime(tmp_path)
    proposal = propose_workspace_search(
        store,
        registry,
        task_id=task.task_id,
        exact_names=["target.py"],
        scope_token="registered_projects",
        proposed_by="qwen35-9b-orion",
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
        no_cloud=True,
        license_state="OWNER",
        revision="sha-b-2",
    )

    called = False

    def runner(*args, **kwargs):
        nonlocal called
        called = True
        return confirmed_runner(*args, **kwargs)

    with pytest.raises(OperatorControlDenied) as exc:
        execute_workspace_search(
            store,
            registry,
            task_id=task.task_id,
            proposal_event_id=proposal.event_id,
            search_runner=runner,
        )

    assert exc.value.code == "workspace_scope_stale"
    assert called is False
    events = store.list_task_events(task.project_id, task.task_id)
    assert [event.event_type for event in events] == [EventType.PROPOSAL]


def test_workspace_execution_replay_is_blocked(tmp_path: Path):
    store, registry, task, _ = make_runtime(tmp_path)
    proposal = propose_workspace_search(
        store,
        registry,
        task_id=task.task_id,
        exact_names=["target.py"],
        scope_token="registered_projects",
        proposed_by="qwen35-9b-orion",
    )
    execute_workspace_search(
        store,
        registry,
        task_id=task.task_id,
        proposal_event_id=proposal.event_id,
        search_runner=confirmed_runner,
    )

    with pytest.raises(OperatorControlDenied) as exc:
        execute_workspace_search(
            store,
            registry,
            task_id=task.task_id,
            proposal_event_id=proposal.event_id,
            search_runner=confirmed_runner,
        )
    assert exc.value.code == "proposal_already_dispatched"


def test_workspace_evidence_cannot_escape_frozen_project_set(tmp_path: Path):
    store, registry, task, _ = make_runtime(tmp_path)
    proposal = propose_workspace_search(
        store,
        registry,
        task_id=task.task_id,
        exact_names=["target.py"],
        scope_token="registered_projects",
        proposed_by="qwen35-9b-orion",
    )

    def escaped_runner(task_id, exact_names, project_ids, trusted_roots):
        evidence, lease = confirmed_runner(
            task_id, exact_names, project_ids, trusted_roots
        )
        result = dict(evidence.result)
        result["searched_locations"] = ["p-a", "p-b"]
        result["matches"] = [
            {
                "location": "p-evil",
                "relative_path": "target.py",
                "name": "target.py",
                "kind": "file",
            }
        ]
        result["match_count"] = 1
        return (
            EvidenceEnvelope(
                task_id=task_id,
                lease_id=evidence.lease_id,
                operation_id=evidence.operation_id,
                implementation_id=evidence.implementation_id,
                outcome=evidence.outcome,
                result=result,
                verifier=evidence.verifier,
            ),
            lease,
        )

    with pytest.raises(OperatorControlDenied) as exc:
        execute_workspace_search(
            store,
            registry,
            task_id=task.task_id,
            proposal_event_id=proposal.event_id,
            search_runner=escaped_runner,
        )
    assert exc.value.code == "workspace_evidence_scope_mismatch"


def test_same_relative_path_in_two_projects_keeps_distinct_identity(tmp_path: Path):
    store, registry, task, _ = make_runtime(tmp_path)
    proposal = propose_workspace_search(
        store,
        registry,
        task_id=task.task_id,
        exact_names=["target.py"],
        scope_token="registered_projects",
        proposed_by="qwen35-9b-orion",
    )

    def same_path_runner(task_id, exact_names, project_ids, trusted_roots):
        return (
            EvidenceEnvelope(
                task_id=task_id,
                lease_id="lease-same",
                operation_id="filesystem.search",
                implementation_id="openjarvis.tool.orion_filesystem_search.v1",
                outcome=Outcome.CONFIRMED,
                result={
                    "operation_id": "filesystem.search",
                    "implementation_id": "openjarvis.tool.orion_filesystem_search.v1",
                    "searched_locations": ["p-a", "p-b"],
                    "matches": [
                        {
                            "location": "p-a",
                            "relative_path": "src/target.py",
                            "name": "target.py",
                            "kind": "file",
                        },
                        {
                            "location": "p-b",
                            "relative_path": "src/target.py",
                            "name": "target.py",
                            "kind": "file",
                        },
                    ],
                    "match_count": 2,
                    "truncated": False,
                },
                verifier="orion.openjarvis.filesystem_search.v1",
            ),
            "lease-same",
        )

    execution = execute_workspace_search(
        store,
        registry,
        task_id=task.task_id,
        proposal_event_id=proposal.event_id,
        search_runner=same_path_runner,
    )

    matches = execution.verified_result["matches"]
    assert matches[0]["relative_path"] == matches[1]["relative_path"]
    assert matches[0]["project_id"] != matches[1]["project_id"]
    assert matches[0]["path_identity_sha256"] != matches[1]["path_identity_sha256"]
