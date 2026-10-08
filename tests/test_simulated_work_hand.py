from dataclasses import replace
from datetime import datetime, timedelta, timezone

from orion_v3.work_loop.authorization import issue_authorization, verify_authorization
from orion_v3.work_loop.contracts import Proposal, RiskClass
from orion_v3.work_loop.executor import ExecutionRequest
from orion_v3.work_loop.simulated_hand import SimulatedWorkHand


def test_simulated_hand_accepts_exact_authorization_but_never_claims_pass(tmp_path):
    p = Proposal("p", "t", "filesystem.write", str(tmp_path))
    secret = b"test-secret"
    token = issue_authorization(p, RiskClass.GREEN, (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat(), secret, source_revision="rev")
    hand = SimulatedWorkHand(secret=secret, source_revision="rev")
    result = hand.execute(ExecutionRequest(p, token))
    assert result.verdict == "indeterminate"
    assert result.source == "orion-simulated-work-hand"
    assert list(tmp_path.iterdir()) == []


def test_simulated_hand_rejects_changed_proposal(tmp_path):
    p = Proposal("p", "t", "filesystem.write", str(tmp_path))
    secret = b"test-secret"
    token = issue_authorization(p, RiskClass.GREEN, (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat(), secret, source_revision="rev")
    changed = replace(p, operation="filesystem.delete")
    result = SimulatedWorkHand(secret=secret, source_revision="rev").execute(ExecutionRequest(changed, token))
    assert result.verdict == "fail"


def test_simulated_hand_rejects_expired_token(tmp_path):
    p = Proposal("p", "t", "filesystem.write", str(tmp_path))
    secret = b"test-secret"
    token = issue_authorization(p, RiskClass.GREEN, (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat(), secret, source_revision="rev")
    assert verify_authorization(token, p, secret, now=datetime.now(timezone.utc) + timedelta(minutes=2)) is False
