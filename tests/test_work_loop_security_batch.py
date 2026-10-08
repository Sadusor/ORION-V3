import math
import pytest
from datetime import datetime, timedelta, timezone
from orion_v3.work_loop.authorization import issue_authorization
from orion_v3.work_loop.contracts import Proposal, RiskClass
from orion_v3.work_loop.independent_observer import observe_read_hash
import hashlib


def test_authorization_far_future_denied(tmp_path):
    p = Proposal("p", "t", "filesystem.read", str(tmp_path))
    with pytest.raises(ValueError):
        issue_authorization(p, RiskClass.GREEN,
            (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(), b"key")


def test_ambiguous_keys_denied(tmp_path):
    p = Proposal("p", "t", "filesystem.read", str(tmp_path), {"nested": {1: "a", "1": "b"}})
    with pytest.raises(ValueError):
        _ = p.proposal_hash


def test_nan_denied(tmp_path):
    p = Proposal("p", "t", "filesystem.read", str(tmp_path), {"value": math.nan})
    with pytest.raises(ValueError):
        _ = p.proposal_hash


def test_independent_read_observation(tmp_path):
    f = tmp_path / "read.txt"
    f.write_bytes(b"hello")
    p = Proposal("p", "t", "filesystem.read", str(tmp_path), {"path": str(f)})
    assert observe_read_hash(p) == hashlib.sha256(b"hello").hexdigest()


def test_observer_rejects_write(tmp_path):
    p = Proposal("p", "t", "filesystem.write", str(tmp_path),
                 {"path": str(tmp_path / "file"), "content": "x"})
    with pytest.raises(ValueError):
        observe_read_hash(p)
