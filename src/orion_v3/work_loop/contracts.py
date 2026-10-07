"""Typed contracts for the minimal Autonomous Work Loop V1."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
import hashlib
import json
from typing import Any


class RiskClass(StrEnum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


@dataclass(frozen=True, slots=True)
class Proposal:
    project_id: str
    task_id: str
    operation: str
    workspace: str
    args: dict[str, Any] = field(default_factory=dict)
    requested_network: bool = False
    requested_install: bool = False
    requested_system_change: bool = False

    def canonical_payload(self) -> bytes:
        return json.dumps(
            asdict(self), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")

    @property
    def proposal_hash(self) -> str:
        return hashlib.sha256(self.canonical_payload()).hexdigest()


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    project_id: str
    task_id: str
    proposal_hash: str
    evidence_type: str
    verdict: str
    source: str
    source_revision: str
    detail: str = ""


@dataclass(slots=True)
class WorkState:
    project_id: str
    objective: str
    checkpoint: str
    current_task: str
    last_verified_result: str = "none"
    next_action: str = ""
    blocked: bool = False
    constraints: list[str] = field(default_factory=list)
    frozen_paths: list[str] = field(default_factory=list)
