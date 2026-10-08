"""Simulation-only model-to-Vault cycle, reusing existing ORION components.

This module accepts model *text* supplied by a caller. It does not invoke Qwen
or allow real execution; the coordinator's Hand is always simulated.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .contracts import WorkState
from .coordinator import WorkLoopCoordinator, CycleOutcome
from .engine import WorkLoopEngine
from .model_proposal import parse_model_proposal
from .vault import ProjectVault


@dataclass(frozen=True, slots=True)
class SimulatedCycle:
    outcome: CycleOutcome
    state: WorkState


def simulate_model_cycle(
    model_text: str,
    *,
    vault: ProjectVault,
    stop,
    secret: bytes,
    source_revision: str,
) -> SimulatedCycle:
    """Use canonical Vault scope, parse a proposal and run a dry-run cycle.

    Caller must supply an already-initialized disposable Vault and trusted STOP.
    Never inject a real executor; coordinator constructs SimulatedWorkHand.
    """
    state = vault.load()
    proposal = parse_model_proposal(
        model_text,
        project_id=state.project_id,
        task_id=state.current_task,
        workspace=str((vault.root / "repo").resolve()),
    )
    coordinator = WorkLoopCoordinator(
        WorkLoopEngine(vault),
        secret=secret,
        source_revision=source_revision,
        stop=stop,
    )
    outcome = coordinator.cycle(proposal)
    return SimulatedCycle(outcome=outcome, state=vault.load())
