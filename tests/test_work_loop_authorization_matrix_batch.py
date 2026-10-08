"""Additional owner authorization mutation tests, no executor involved."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import pytest
from orion_v3.work_loop.authorization import issue_authorization, verify_authorization
from orion_v3.work_loop.contracts import Proposal, RiskClass

@pytest.fixture
def case(tmp_path):
    p = Proposal("demo", "task", "filesystem.read", str(tmp_path / "repo"))
    key = b"test-secret"
    expiry = (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat()
    a = issue_authorization(p, RiskClass.GREEN, expiry, key, source_revision="revision")
    return p, key, a

@pytest.mark.parametrize("field", ["project_id", "task_id", "proposal_hash", "signature", "source_revision", "nonce"])
def test_modified_authorization_is_denied(case, field):
    proposal, secret, auth = case
    assert verify_authorization(auth, proposal, secret, expected_source_revision="revision")
    changed = replace(auth, **{field: "modified"})
    assert not verify_authorization(changed, proposal, secret, expected_source_revision="revision")

@pytest.mark.parametrize("minutes", [-1, 6, 60])
def test_outside_expiry_window_denied(case, minutes):
    proposal, secret, auth = case
    now = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    assert not verify_authorization(auth, proposal, secret, now=now, expected_source_revision="revision")
