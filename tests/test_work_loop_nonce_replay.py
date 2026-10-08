from datetime import datetime, timedelta, timezone

from orion_v3.work_loop.authorization import issue_authorization
from orion_v3.work_loop.contracts import Proposal, RiskClass
from orion_v3.work_loop.executor import ExecutionRequest
from orion_v3.work_loop.nonce_store import NonceStore
from orion_v3.work_loop.simulated_hand import SimulatedWorkHand


def test_nonce_replay_rejected_across_instances(tmp_path):
    p = Proposal("p", "t", "filesystem.read", str(tmp_path))
    secret = b"test"
    auth = issue_authorization(p, RiskClass.GREEN,
        (datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat(), secret, source_revision="rev")
    path = tmp_path / "nonces.sqlite3"
    first = SimulatedWorkHand(secret=secret, source_revision="rev", nonce_store=NonceStore(path))
    assert first.execute(ExecutionRequest(p, auth)).verdict == "indeterminate"
    second = SimulatedWorkHand(secret=secret, source_revision="rev", nonce_store=NonceStore(path))
    assert second.execute(ExecutionRequest(p, auth)).verdict == "fail"


def test_invalid_auth_does_not_consume_nonce(tmp_path):
    from dataclasses import replace
    p = Proposal("p", "t", "filesystem.read", str(tmp_path))
    auth = issue_authorization(p, RiskClass.GREEN,
        (datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat(), b"right", source_revision="rev")
    hand = SimulatedWorkHand(secret=b"right", source_revision="rev",
                             nonce_store=NonceStore(tmp_path / "nonces.sqlite3"))
    assert hand.execute(ExecutionRequest(p, replace(auth, signature="0"*64))).verdict == "fail"
    assert hand.execute(ExecutionRequest(p, auth)).verdict == "indeterminate"
