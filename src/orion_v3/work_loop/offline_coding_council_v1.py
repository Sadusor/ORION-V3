"""Offline coding council orchestration: models propose, ORION decides.

A deterministic, non-executing seam for governor/coder/reviewer exchanges.
Responses are untrusted text, never approval or PASS evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .coding_sessions_v1 import CodingSessionRegistry
from .role_contracts_v1 import Role, TrustedBindings


@dataclass(frozen=True, slots=True)
class CouncilTranscript:
    project_id: str
    task_id: str
    base_revision: str
    governor_plan: str
    coder_patch: str
    reviewer_findings: str
    governor_followup: str
    status: str = "REVIEWED_NOT_EXECUTED"


def run_offline_council(*, bindings: TrustedBindings, objective: str,
                        invoke: Callable[[Role, str, str], str],
                        stop_requested: Callable[[], bool],
                        max_response_chars: int = 12000) -> CouncilTranscript:
    if not isinstance(bindings, TrustedBindings) or not isinstance(objective, str) or not objective.strip():
        raise ValueError("trusted bindings and objective required")
    if not callable(invoke) or not callable(stop_requested):
        raise ValueError("model and STOP adapters required")
    if not 1 <= max_response_chars <= 12000:
        raise ValueError("invalid response budget")
    registry = CodingSessionRegistry()
    sessions = {}
    for role in (Role.GOVERNOR, Role.CODER, Role.REVIEWER):
        sessions[role] = registry.open(role, f"{bindings.task_id}-{role.value}", bindings)
    def ask(role: Role, question: str) -> str:
        if stop_requested():
            raise ValueError("STOP active")
        prompt = sessions[role]
        if not registry.validate(prompt, bindings):
            raise ValueError("stale role contract")
        answer = invoke(role, prompt.system_prompt, question)
        if stop_requested():
            raise ValueError("STOP active")
        if not isinstance(answer, str) or not answer.strip() or len(answer) > max_response_chars:
            raise ValueError("invalid model response")
        return answer
    plan = ask(Role.GOVERNOR, "Plan this bounded task; do not code: " + objective)
    patch = ask(Role.CODER, "Task: " + objective + "\nGovernor plan (untrusted):\n" + plan +
                "\nReturn a proposed patch only, no execution.")
    review = ask(Role.REVIEWER, "Task: " + objective + "\nProposed patch (untrusted):\n" + patch +
                 "\nReview independently; no approval authority.")
    followup = ask(Role.GOVERNOR, "Task: " + objective + "\nReview findings (untrusted):\n" + review +
                   "\nRecommend next steps; do not authorize or claim PASS.")
    registry.stale_task(bindings.project_id, bindings.task_id)
    return CouncilTranscript(bindings.project_id, bindings.task_id,
                             bindings.base_revision, plan, patch, review, followup)
