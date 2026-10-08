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


def stage(label: str, message: str) -> None:
    print(f"\n[{label}] {message}", flush=True)


def main() -> None:
    stage("01/07", "Checking local Ollama and required Qwen 9B model")
    brain = LocalBrainModule(preferred_model="qwen3.5-9b-orion")
    models = brain._available_models()
    print("OLLAMA MODELS> " + json.dumps(models), flush=True)
    matches = [name for name in models if "qwen" in name.lower() and "9b" in name.lower()]
    if len(matches) != 1:
        raise RuntimeError("Need exactly one Qwen 9B model; available matches: " + repr(matches))
    selected_model = matches[0]
    print("SELECTED MODEL> " + selected_model, flush=True)
    stage("02/07", "Creating disposable Vault; no project files will be changed")
    with tempfile.TemporaryDirectory(prefix="orion-qwen-readonly-", dir=str(Path.cwd())) as directory:
        vault = ProjectVault(Path(directory) / "vault")
        vault.initialize(WorkState(
            project_id="qwen-smoke", objective="Inspect Git working tree without changing files",
            checkpoint="Before read-only proposal", current_task="Propose git.status only",
            constraints=["No execution", "No network access by proposed operation", "No file changes"],
        ))
        state = vault.load()
        print("VAULT TASK> " + state.current_task, flush=True)
        print("VAULT OBJECTIVE> " + state.objective, flush=True)
        print("VAULT CONSTRAINTS> " + "; ".join(state.constraints), flush=True)
        before = vault.state_path.read_bytes()
        stage("03/07", "Sending bounded proposal request to real Qwen; waiting for response")
        proposal = propose_from_local_qwen(vault, brain=brain, model=selected_model)
        stage("04/07", "Qwen response received; displaying typed proposal")
        risk = classify_proposal(proposal)
        print("MODEL> " + selected_model)
        print("PROPOSAL> " + json.dumps({"operation": proposal.operation, "args": proposal.args,
              "requested_network": proposal.requested_network, "requested_install": proposal.requested_install,
              "requested_system_change": proposal.requested_system_change}, ensure_ascii=False))
        stage("05/07", "ORION policy classification")
        print("POLICY> " + risk.risk.value, flush=True)
        print("POLICY REASON> " + risk.reason, flush=True)
        stage("06/07", "Checking canonical Vault unchanged and workspace untouched")
        assert proposal.project_id == "qwen-smoke"
        assert proposal.task_id == "Propose git.status only"
        assert vault.state_path.read_bytes() == before
        assert vault.load().last_verified_result == "none"
        assert not list(vault.repo_path.iterdir())
        if proposal.operation != "git.status" or proposal.args or risk.risk.value != "green":
            raise RuntimeError("Model proposal was not the expected GREEN git.status; no execution occurred")
        stage("07/07", "Verification complete")
        print("ORION_QWEN_READONLY> PASS; PROPOSAL_ONLY; NOTHING_EXECUTED", flush=True)


if __name__ == "__main__":
    main()
