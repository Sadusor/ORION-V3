"""Physical demo of ORION's existing simulated coordinator and fail-closed verifier.

Disposable Vault only; no native Hand, model calls or calculator file writes.
"""
from __future__ import annotations
from dataclasses import replace
from pathlib import Path
import tempfile
from orion_v3.work_loop.contracts import WorkState, EvidenceRecord
from orion_v3.work_loop.vault import ProjectVault
from orion_v3.work_loop.engine import WorkLoopEngine
from orion_v3.work_loop.coordinator import WorkLoopCoordinator
from tiny_calculator_preview import build_proposal

class NeverStopped:
    def stop_requested(self)->bool:return False

class AlwaysStopped:
    def stop_requested(self)->bool:return True

def main():
    with tempfile.TemporaryDirectory(prefix="orion-tiny-sim-") as directory:
        root=Path(directory)
        vault=ProjectVault(root)
        vault.initialize(WorkState(project_id="tiny-calculator",
            objective="Test calculator in simulation only",
            checkpoint="simulation",current_task="add-two-numbers",
            frozen_paths=["protected.py"]))
        proposal=build_proposal(str(vault.repo_path))
        engine=WorkLoopEngine(vault)
        coordinator=WorkLoopCoordinator(engine,secret=b"tiny-demo-ephemeral-key-only",
            source_revision="tiny-calculator-sim-v1",stop=NeverStopped())
        result=coordinator.cycle(proposal)
        print("TINY_SIM> COORDINATOR_STATUS",result.status,flush=True)
        print("TINY_SIM> COORDINATOR_REASON",result.reason,flush=True)
        assert result.status in ("blocked","dry_run"),result
        assert result.evidence is not None
        assert result.evidence.verdict=="indeterminate",result.evidence
        print("TINY_SIM> EVIDENCE",result.evidence.verdict,result.evidence.source,flush=True)
        state=vault.load()
        assert state.last_verified_result=="execution:indeterminate",state
        assert state.blocked is True,state
        assert not (vault.repo_path/"calculator.py").exists()
        assert not (vault.repo_path/"test_calculator.py").exists()
        print("TINY_SIM> NO_FALSE_PASS_NO_FILES PASS",flush=True)
        # Forged PASS from a simulated executor must never promote canonical state.
        forged=replace(result.evidence,verdict="pass")
        check=engine.apply_evidence(proposal,forged,required_type="execution",
            expected_source_revision="tiny-calculator-sim-v1",
            next_action_on_pass="WRONG",next_action_on_fail="WRONG",
            trusted_verifier_pass=True)
        assert not check.state_updated,check
        assert vault.load().last_verified_result=="execution:indeterminate"
        print("TINY_SIM> FORGED_PASS_DENIED",check.verification.reason,flush=True)
        stopped=WorkLoopCoordinator(engine,secret=b"tiny-demo-ephemeral-key-only",
            source_revision="tiny-calculator-sim-v1",stop=AlwaysStopped()).cycle(proposal)
        assert stopped.status=="stopped"
        print("TINY_SIM> PRE_REQUEST_STOP_PASS",flush=True)
        assert not (vault.repo_path/"calculator.py").exists()
        print("TINY_SIM> SIMULATION_GATE_PASS_NO_NATIVE_EXECUTION",flush=True)

if __name__=="__main__":main()
