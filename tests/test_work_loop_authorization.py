from datetime import datetime, timedelta, timezone

import pytest

from orion_v3.work_loop.authorization import issue_authorization, verify_authorization
from orion_v3.work_loop.contracts import Proposal, RiskClass


SECRET = b"test-only-secret"


def p(text="one"):
    return Proposal("p", "t", "filesystem.write", "/work", {"path": "x", "text": text})


def future():
    return (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()


def test_authorization_is_bound_to_exact_proposal():
    original = p()
    auth = issue_authorization(original, RiskClass.GREEN, future(), SECRET)
    assert verify_authorization(auth, original, SECRET)
    assert not verify_authorization(auth, p("changed"), SECRET)


def test_red_cannot_be_authorized():
    with pytest.raises(ValueError):
        issue_authorization(p(), RiskClass.RED, future(), SECRET)


def test_expired_authorization_fails():
    proposal = p()
    expired = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    with pytest.raises(ValueError, match="authorization expiry"):
        issue_authorization(proposal, RiskClass.GREEN, expired, SECRET)
