"""Exact-proposal authorization tokens inspired by the audited OpenMuse pattern."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import hashlib
import hmac
import json
import secrets

from .contracts import Proposal, RiskClass


@dataclass(frozen=True, slots=True)
class Authorization:
    project_id: str
    task_id: str
    proposal_hash: str
    risk: RiskClass
    expires_at: str
    nonce: str
    signature: str


def _payload(project_id: str, task_id: str, proposal_hash: str, risk: RiskClass, expires_at: str, nonce: str) -> bytes:
    return json.dumps(
        [project_id, task_id, proposal_hash, risk.value, expires_at, nonce],
        separators=(",", ":"),
    ).encode("utf-8")


def issue_authorization(proposal: Proposal, risk: RiskClass, expires_at: str, secret: bytes) -> Authorization:
    if risk == RiskClass.RED:
        raise ValueError("RED proposals cannot be authorized")
    expiry = datetime.fromisoformat(expires_at)
    now = datetime.now(timezone.utc)
    if expiry.tzinfo is None or not now < expiry <= now + timedelta(minutes=5):
        raise ValueError('authorization expiry must be within five minutes')
    nonce = secrets.token_hex(16)
    signature = hmac.new(
        secret,
        _payload(proposal.project_id, proposal.task_id, proposal.proposal_hash, risk, expires_at, nonce),
        hashlib.sha256,
    ).hexdigest()
    return Authorization(proposal.project_id, proposal.task_id, proposal.proposal_hash, risk, expires_at, nonce, signature)


def verify_authorization(auth: Authorization, proposal: Proposal, secret: bytes, now: datetime | None = None) -> bool:
    if auth.project_id != proposal.project_id or auth.task_id != proposal.task_id:
        return False
    if auth.proposal_hash != proposal.proposal_hash or auth.risk == RiskClass.RED:
        return False
    try:
        expiry = datetime.fromisoformat(auth.expires_at)
    except ValueError:
        return False
    if expiry.tzinfo is None:
        return False
    now = now or datetime.now(timezone.utc)
    if expiry <= now or expiry > now + timedelta(minutes=5):
        return False
    expected = hmac.new(
        secret,
        _payload(auth.project_id, auth.task_id, auth.proposal_hash, auth.risk, auth.expires_at, auth.nonce),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(auth.signature, expected)
