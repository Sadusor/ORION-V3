"""Physical read-only Qwen proposal smoke test. Never invokes a Hand."""
from __future__ import annotations
import json
import tempfile
from pathlib import Path

from orion_v3.modules.local_brain import LocalBrainModule
from orion_v3.work_loop.contracts import WorkState
from orion_v3.work_loop.local_proposer import propose_from_local_qwen
from orion_v3.work_loop.policy import classify_proposal
from orion_v3.work_loop.vault import ProjectVault


def main() -> None:
    brain = LocalBrainModule(preferred_model="qwen3.5-9b-orion")
    models = brain._available_models()
    if "qwen3.5-9b-orion" not in models:
        raise RuntimeError("Expected qwen3.5-9b-orion missing; no fallback model allowed")
    with tempfile.TemporaryDirectory(prefix="orion-qwen-readonly-", dir=str(Path.cwd())) as directory:
        vault = ProjectVault(Path(directory) / "vault")
        vault.initialize(WorkState(
            project_id="qwen-smoke", objective="Inspect Git working tree without changing files",
            checkpoint="Before read-only proposal", current_task="Propose git.status only",
            constraints=["No execution", "No network access by proposed operation", "No file changes"],
        ))
        before = vault.state_path.read_bytes()
        proposal = propose_from_local_qwen(vault, brain=brain, model="qwen3.5-9b-orion")
        risk = classify_proposal(proposal)
        print("MODEL> qwen3.5-9b-orion")
        print("PROPOSAL> " + json.dumps({"operation": proposal.operation, "args": proposal.args,
              "requested_network": proposal.requested_network, "requested_install": proposal.requested_install,
              "requested_system_change": proposal.requested_system_change}, ensure_ascii=False))
        print("POLICY> " + risk.risk.value)
        assert proposal.project_id == "qwen-smoke"
        assert proposal.task_id == "Propose git.status only"
        assert vault.state_path.read_bytes() == before
        assert vault.load().last_verified_result == "none"
        assert not list(vault.repo_path.iterdir())
        if proposal.operation != "git.status" or proposal.args or risk.risk.value != "green":
            raise RuntimeError("Model proposal was not the expected GREEN git.status; no execution occurred")
        print("ORION_QWEN_READONLY> PASS; PROPOSAL_ONLY; NOTHING_EXECUTED")


if __name__ == "__main__":
    main()
