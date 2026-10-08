"""Offline provider-callback bridge test; no API keys, cloud network or execution."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from orion_v3.work_loop.cloud_model_bridge import request_cloud_proposal, review_cloud_proposal
from orion_v3.work_loop.contracts import WorkState
from orion_v3.work_loop.engine import WorkLoopEngine
from orion_v3.work_loop.vault import ProjectVault

with TemporaryDirectory(prefix="orion-cloud-bridge-") as root:
    vault = ProjectVault(Path(root) / "vault")
    vault.initialize(WorkState("cloud-project", "bounded cloud test", "initial", "repair-1"))
    engine = WorkLoopEngine(vault)
    workspace = Path(root) / "workspace"
    workspace.mkdir()
    payload = dict(project_id="cloud-project", task_id="repair-1",
                   operation="filesystem.write", workspace=str(workspace),
                   args={"path": str(workspace / "approved.txt"), "content": "fixed"},
                   requested_network=False, requested_install=False,
                   requested_system_change=False)
    prompts = []
    def coder(prompt):
        prompts.append(prompt)
        return json.dumps(payload)
    suggestion = request_cloud_proposal(provider="fixture-coder", invoke=coder,
                                        engine=engine, task_brief="Fix bounded fixture")
    assert suggestion.proposal.args["content"] == "fixed"
    assert "Canonical project_id" in prompts[0]
    print("M4_CLOUD> INJECTED_CODER_PROPOSAL_POLICY_PASS")
    review = review_cloud_proposal(provider="fixture-reviewer",
                                   invoke=lambda prompt: "Advisory: inspect exact bytes.",
                                   proposal=suggestion.proposal)
    assert "Advisory" in review
    print("M4_CLOUD> INDEPENDENT_REVIEWER_ADVISORY_PASS")
    for change in ({"project_id": "other"}, {"requested_network": True},
                   {"operation": "stop.modify", "args": {}}):
        bad = dict(payload, **change)
        try:
            request_cloud_proposal(provider="fixture-coder", invoke=lambda prompt: json.dumps(bad),
                                   engine=engine, task_brief="Fix bounded fixture")
        except ValueError:
            pass
        else:
            raise AssertionError("unsafe provider proposal accepted")
    print("M4_CLOUD> THREE_CLOUD_ATTACKS_DENIED_PASS")
    assert vault.load().last_verified_result == "none"
    print("M4_CLOUD> NO_EXECUTION_NO_VAULT_MUTATION_PASS")
    print("M4_CLOUD> REAL_PROVIDER_CONNECTION_NOT_YET_QUALIFIED")
