"""Deterministic offline contract checks for Qwen proposal adapter; no model/network."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from orion_v3.work_loop.contracts import WorkState
from orion_v3.work_loop.engine import WorkLoopEngine
from orion_v3.work_loop.qwen_proposal_adapter import parse_qwen_proposal
from orion_v3.work_loop.vault import ProjectVault

with TemporaryDirectory(prefix="orion-m4-adapter-") as root:
    vault = ProjectVault(Path(root) / "vault")
    vault.initialize(WorkState("m4-test", "bounded adapter", "adapter", "task-1"))
    engine = WorkLoopEngine(vault)
    workspace = str(Path(root) / "workspace")
    Path(workspace).mkdir()
    payload = dict(project_id="m4-test", task_id="task-1", operation="filesystem.write",
                   workspace=workspace, args={"path": str(Path(workspace) / "fixture.txt"), "content": "ok"},
                   requested_network=False, requested_install=False, requested_system_change=False)
    proposal = parse_qwen_proposal(json.dumps(payload), engine)
    assert proposal.project_id == "m4-test"
    print("M4_QWEN_ADAPTER> BOUNDED_GREEN_PASS")
    negatives = [
        dict(payload, project_id="other"),
        dict(payload, requested_network=True),
        dict(payload, requested_system_change=True),
        dict(payload, args={"path": str(Path(root) / "escape.txt"), "content": "bad"}),
        dict(payload, operation="stop.modify", args={}),
    ]
    for candidate in negatives:
        try:
            parse_qwen_proposal(json.dumps(candidate), engine)
        except ValueError:
            pass
        else:
            raise AssertionError("malicious proposal was accepted")
    for raw in ['{"project_id":"a","project_id":"b"}', "[]", "{}", "x" * 9000]:
        try:
            parse_qwen_proposal(raw, engine)
        except (ValueError, json.JSONDecodeError):
            pass
        else:
            raise AssertionError("malformed model response accepted")
    print("M4_QWEN_ADAPTER> NINE_NEGATIVE_CASES_DENIED_PASS")
    assert vault.load().last_verified_result == "none"
    print("M4_QWEN_ADAPTER> NO_EXECUTION_NO_VAULT_MUTATION_PASS")
