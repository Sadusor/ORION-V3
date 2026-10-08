"""Offline ORION-native engineering collaboration protocol.

This module records proposals and reviews; it grants no execution authority.
"""
from dataclasses import dataclass, replace
from enum import StrEnum
from hashlib import sha256
import json


class Stage(StrEnum):
    TASK = "task"
    PROPOSED = "proposed"
    REVIEWED = "reviewed"
    OWNER_APPROVED = "owner_approved"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class EngineeringCycle:
    project_id: str
    task_id: str
    objective: str
    stage: Stage = Stage.TASK
    proposal: str = ""
    review: str = ""

    @property
    def proposal_digest(self) -> str:
        payload = json.dumps(
            [self.project_id, self.task_id, self.objective, self.proposal],
            ensure_ascii=False, separators=(",", ":"),
        )
        return sha256(payload.encode("utf-8")).hexdigest()

    def submit_proposal(self, proposal: str) -> "EngineeringCycle":
        if self.stage != Stage.TASK or not proposal.strip():
            raise ValueError("expected an open task and nonempty proposal")
        return replace(self, proposal=proposal, stage=Stage.PROPOSED)

    def submit_review(self, review: str) -> "EngineeringCycle":
        if self.stage != Stage.PROPOSED or not review.strip():
            raise ValueError("expected a proposal and nonempty review")
        return replace(self, review=review, stage=Stage.REVIEWED)

    def owner_decide(self, decision: str, proposal_digest: str) -> "EngineeringCycle":
        if self.stage != Stage.REVIEWED or proposal_digest != self.proposal_digest:
            raise ValueError("owner decision requires reviewed, matching proposal")
        if decision == "approve":
            return replace(self, stage=Stage.OWNER_APPROVED)
        if decision == "reject":
            return replace(self, stage=Stage.REJECTED)
        raise ValueError("unknown owner decision")
