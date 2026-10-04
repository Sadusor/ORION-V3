from pathlib import Path

from orion_v3.operator import (
    ApprovalStatus,
    OperatorControlPlane,
    dispatch_governor_tool,
    governor_control_tool_specs,
)
from orion_v3.state import EventType, OrionStateStore


def make_runtime(tmp_path: Path):
    store = OrionStateStore(tmp_path / "orion.db")
    store.initialize()
    project = store.create_project("Governor Surface", project_id="project-gov")
    task = store.create_task(project.project_id, "Governor task", task_id="task-gov")
    control = OperatorControlPlane(store)
    control.initialize()
    return store, control, task


def test_governor_tools_are_registry_derived_and_not_raw_hands():
    tools = governor_control_tool_specs()
    names = {
        item["function"]["name"]
        for item in tools
    }

    assert "orion_capability_fs__search_exact" in names
    assert "orion_capability_project__publish_exact_artifact" in names
    assert "orion_request_cloud_specialist" in names
    assert "orion_resume_approved_action" in names

    encoded = repr(tools)
    assert "FileEditorTool" not in encoded
    assert "PowerShell" not in encoded
    assert "subprocess" not in encoded


def test_read_only_governor_proposal_is_validated_and_recorded(tmp_path: Path):
    store, control, task = make_runtime(tmp_path)

    result = dispatch_governor_tool(
        control,
        task_id=task.task_id,
        tool_name="orion_capability_fs__search_exact",
        arguments={
            "exact_names": ["README.md"],
            "locations": ["active_project"],
        },
        actor_id="qwen35-9b-orion",
    )

    assert result["kind"] == "capability_proposal"
    assert result["status"] == "PROPOSED"
    assert result["capability_id"] == "fs.search_exact"
    assert result["params"] == {
        "exact_names": ["README.md"],
        "locations": ["active_project"],
        "recursive": True,
        "max_depth": 4,
        "max_results": 50,
        "reveal_containing_folders": False,
    }

    events = store.list_task_events(task.project_id, task.task_id)
    assert len(events) == 1
    assert events[0].event_type == EventType.PROPOSAL
    assert events[0].payload["kind"] == "capability_action_proposed"
    assert events[0].payload["action_sha256"] == result["action_sha256"]


def test_governor_approval_and_resume_use_exact_frozen_action(tmp_path: Path):
    _, control, task = make_runtime(tmp_path)

    requested = dispatch_governor_tool(
        control,
        task_id=task.task_id,
        tool_name="orion_capability_project__publish_exact_artifact",
        arguments={
            "artifact_path": "docs/governor.txt",
            "artifact_content": "exact approved bytes\n",
        },
        actor_id="qwen35-9b-orion",
    )

    assert requested["kind"] == "approval_request"
    assert requested["status"] == ApprovalStatus.PENDING.value
    approval_id = requested["approval_id"]
    frozen_hash = requested["action_sha256"]

    control.approve(approval_id, approved_by="owner")

    resumed = dispatch_governor_tool(
        control,
        task_id=task.task_id,
        tool_name="orion_resume_approved_action",
        arguments={"approval_id": approval_id},
        actor_id="qwen35-9b-orion",
    )

    assert resumed["status"] == ApprovalStatus.CONSUMED.value
    assert resumed["action_sha256"] == frozen_hash
    assert resumed["params"] == {
        "artifact_path": "docs/governor.txt",
        "artifact_content": "exact approved bytes\n",
    }


def test_governor_cloud_request_enters_orion_queue(tmp_path: Path):
    _, control, task = make_runtime(tmp_path)

    queued = dispatch_governor_tool(
        control,
        task_id=task.task_id,
        tool_name="orion_request_cloud_specialist",
        arguments={
            "specialty": "coding",
            "task": "Refactor a multi-module parser and update tests.",
        },
        actor_id="qwen35-9b-orion",
    )

    assert queued["kind"] == "cloud_specialist_request"
    assert queued["status"] == "QUEUED"
    assert queued["recipient"] == "cloud:coding"
    assert queued["specialty"] == "coding"
