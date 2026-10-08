"""Transaction identity is deterministic, scoped and never an authorization token."""
from dataclasses import replace
import pytest
from orion_v3.work_loop.transaction_identity import TransactionIdentity


@pytest.fixture
def identity():
    return TransactionIdentity("p", "t", "a" * 64, "rev", "execution", "fail")


def test_digest_is_stable(identity):
    assert identity.digest == replace(identity).digest
    assert len(identity.digest) == 64


@pytest.mark.parametrize("field,value", [
    ("project_id", "other"),
    ("task_id", "other"),
    ("proposal_hash", "b" * 64),
    ("source_revision", "next"),
    ("evidence_type", "test"),
    ("verdict", "indeterminate"),
])
def test_every_bound_dimension_changes_digest(identity, field, value):
    assert replace(identity, **{field: value}).digest != identity.digest


@pytest.mark.parametrize("field,value", [
    ("project_id", ""),
    ("task_id", ""),
    ("source_revision", ""),
    ("proposal_hash", "not-a-hash"),
    ("evidence_type", "invented"),
    ("verdict", "approved"),
])
def test_invalid_identity_rejected(identity, field, value):
    with pytest.raises(ValueError):
        replace(identity, **{field: value})
