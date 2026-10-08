"""Calculator milestone simulation using the existing coordinator and Vault.

No local model, subprocess, or filesystem mutation outside TemporaryDirectory.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from .contracts import Proposal, WorkState
from .coordinator import WorkLoopCoordinator
from .engine import WorkLoopEngine
from .vault import ProjectVault


class _NoStop:
    def stop_requested(self) -> bool:
        return False


def simulate_calculator_milestone() -> dict[str, str]:
    with TemporaryDirectory(prefix="orion-calculator-sim-") as temp:
        root = Path(temp) / "calculator"
        vault = ProjectVault(root)
        vault.initialize(WorkState(
            project_id="calculator-simulation",
            objective="Repair add(2,3) to return 5",
            checkpoint="calculator fixture prepared",
            current_task="fix-add",
            frozen_paths=[str(root / "repo" / "FROZEN.txt")],
        ))
        coordinator = WorkLoopCoordinator(
            WorkLoopEngine(vault), secret=b"simulation-only-secret",
            source_revision="calculator-simulation-v1", stop=_NoStop(),
        )
        proposal = Proposal(
            project_id="calculator-simulation", task_id="fix-add",
            operation="filesystem.write", workspace=str(root / "repo"),
            args={"path": str(root / "repo" / "calculator.py"), "content": "def add(a, b):\n    return a + b\n"},
        )
        outcome = coordinator.cycle(proposal)
        state = vault.load()
        return {
            "status": outcome.status,
            "evidence_verdict": outcome.evidence.verdict if outcome.evidence else "none",
            "last_verified_result": state.last_verified_result,
            "blocked": str(state.blocked).lower(),
            "source_written": str((root / "repo" / "calculator.py").exists()).lower(),
        }


if __name__ == "__main__":
    for key, value in simulate_calculator_milestone().items():
        print(f"{key.upper()}> {value}")
