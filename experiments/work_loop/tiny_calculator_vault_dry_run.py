"""ORION-native Tiny Calculator authority dry-run.

Runs in a temporary disposable Vault; no native Hand or source writes.
"""
from __future__ import annotations
import json
import tempfile
from pathlib import Path
from orion_v3.work_loop.contracts import WorkState
from orion_v3.work_loop.vault import ProjectVault
from orion_v3.work_loop.engine import WorkLoopEngine
from tiny_calculator_preview import build_proposal

def main():
    with tempfile.TemporaryDirectory(prefix="orion-tiny-calculator-") as directory:
        root=Path(directory)
        workspace=str(root/"repo")
        vault=ProjectVault(root)
        vault.initialize(WorkState(project_id="tiny-calculator",
            objective="Add two integers in a disposable calculator project",
            checkpoint="dry-run",current_task="add-two-numbers",
            next_action="review proposed calculator code",
            frozen_paths=["protected.py"]))
        proposal=build_proposal(workspace)
        engine=WorkLoopEngine(vault)
        prepared=engine.prepare(proposal)
        print("TINY_DEMO> POLICY",prepared.policy.risk.value,prepared.policy.reason,flush=True)
        if prepared.policy.risk.value!="green":raise SystemExit("policy rejected calculator")
        # Deliberately do not invoke a Hand or grant native execution.
        print("TINY_DEMO> PROPOSAL_HASH",proposal.proposal_hash,flush=True)
        print("TINY_DEMO> HAND_NOT_INVOKED",flush=True)
        print("TINY_DEMO> NATIVE_EXECUTION_NOT_AUTHORIZED",flush=True)
        print("TINY_DEMO> VAULT_STATE",vault.load().checkpoint,flush=True)
        print("TINY_DEMO> NO_CALCULATOR_FILE_WRITTEN",not (root/"repo"/"calculator.py").exists(),flush=True)
        if (root/"repo"/"calculator.py").exists():raise SystemExit("unexpected write")
        print("TINY_DEMO> DRY_RUN_PREFLIGHT_PASS",flush=True)

if __name__=="__main__":main()
