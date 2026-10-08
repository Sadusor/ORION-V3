"""Provider-neutral multi-AI plan gate. Advisory only: no execution or authority."""
from dataclasses import dataclass, replace
from hashlib import sha256
import json

@dataclass(frozen=True)
class MultiAIPlan:
    project_id: str
    task_id: str
    objective: str
    proposals: tuple = ()
    critiques: tuple = ()
    plan: str = ""
    disagreements: tuple = ()
    approved_digest: str = ""
    stage: str = "brainstorm"

    def _digest(self):
        payload = [self.project_id, self.task_id, self.objective,
                   self.proposals, self.critiques, self.plan, self.disagreements]
        return sha256(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()

    @property
    def plan_digest(self):
        return self._digest()

    def submit_independent(self, contributions):
        if self.stage != "brainstorm" or self.proposals:
            raise ValueError("independent round closed")
        if len(contributions) < 2:
            raise ValueError("at least two models required")
        names = [name for name, _ in contributions]
        if len(set(names)) != len(names) or any(not isinstance(name, str) or not name.strip() for name in names):
            raise ValueError("distinct model identities required")
        if any(not isinstance(body, str) or not body.strip() for _, body in contributions):
            raise ValueError("nonempty proposals required")
        return replace(self, proposals=tuple(contributions), stage="critique")

    def submit_cross_review(self, reviews):
        if self.stage != "critique":
            raise ValueError("wrong stage")
        expected = {name for name, _ in self.proposals}
        if len(reviews) != len(expected) or {name for name, _ in reviews} != expected:
            raise ValueError("each independent model must review")
        if any(not isinstance(body, str) or not body.strip() for _, body in reviews):
            raise ValueError("nonempty critiques required")
        return replace(self, critiques=tuple(reviews), stage="plan")

    def propose_plan(self, plan, disagreements=()):
        if self.stage != "plan" or not isinstance(plan, str) or not plan.strip():
            raise ValueError("reviewed nonempty plan required")
        if any(not isinstance(x, str) or not x.strip() for x in disagreements):
            raise ValueError("invalid disagreement")
        return replace(self, plan=plan, disagreements=tuple(disagreements), stage="owner_review")

    def owner_decide(self, decision, digest):
        if self.stage != "owner_review" or digest != self.plan_digest:
            raise ValueError("stale or unauthorized decision")
        if decision == "approve":
            return replace(self, approved_digest=digest, stage="approved_for_patch_proposals")
        if decision == "reject":
            return replace(self, stage="rejected")
        raise ValueError("unknown owner decision")
