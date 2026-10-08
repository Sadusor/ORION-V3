"""Offline contract tests; no real execution or model connections."""
import pytest

from orion_v3.work_loop.engineering_cycle import EngineeringCycle, Stage


def test_reviewed_proposal_requires_explicit_owner_decision():
    cycle = EngineeringCycle("project", "task", "bounded test")
    proposed = cycle.submit_proposal("create one fixture")
    reviewed = proposed.submit_review("scope is narrow")
    assert reviewed.stage == Stage.REVIEWED
    assert reviewed.owner_decide("approve", reviewed.proposal_digest).stage == Stage.OWNER_APPROVED


def test_review_does_not_grant_authority():
    reviewed = EngineeringCycle("p", "t", "task").submit_proposal("code").submit_review("looks good")
    assert reviewed.stage != Stage.OWNER_APPROVED
    assert not hasattr(reviewed, "execute")


def test_rejects_stale_or_forged_proposal_digest():
    reviewed = EngineeringCycle("p", "t", "task").submit_proposal("code").submit_review("ok")
    with pytest.raises(ValueError):
        reviewed.owner_decide("approve", "stale")


def test_rejects_missing_review_and_invalid_transition():
    cycle = EngineeringCycle("p", "t", "task")
    with pytest.raises(ValueError):
        cycle.submit_review("ok")
    with pytest.raises(ValueError):
        cycle.owner_decide("approve", cycle.proposal_digest)


def test_rejects_empty_and_unknown_decisions():
    cycle = EngineeringCycle("p", "t", "task")
    with pytest.raises(ValueError):
        cycle.submit_proposal(" ")
    reviewed = cycle.submit_proposal("code").submit_review("review")
    with pytest.raises(ValueError):
        reviewed.owner_decide("maybe", reviewed.proposal_digest)


def test_rejects_second_proposal_after_review():
    reviewed = EngineeringCycle("p", "t", "task").submit_proposal("code").submit_review("review")
    with pytest.raises(ValueError):
        reviewed.submit_proposal("altered")
