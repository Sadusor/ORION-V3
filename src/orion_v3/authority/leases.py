from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from secrets import token_urlsafe
from time import time
from typing import Any, Callable, Mapping


class LeaseDenied(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ActionLease:
    lease_id: str
    task_id: str
    operation_id: str
    principal: str
    scope: Mapping[str, Any]
    issued_at: float
    expires_at: float


@dataclass(frozen=True)
class IssuedLease:
    """Opaque credential plus the human/audit descriptor it authorizes."""

    token: str
    lease: ActionLease


@dataclass
class _LeaseRecord:
    lease: ActionLease
    token_hash: str
    revoked: bool = False


class LeaseAuthority:
    """ORION-owned short-lived authority store for Gate 1.

    The substrate receives an opaque token. It cannot mint, widen or renew
    authority because only this object owns valid token hashes.
    """

    def __init__(
        self,
        *,
        clock: Callable[[], float] = time,
        token_factory: Callable[[], str] | None = None,
    ) -> None:
        self._clock = clock
        self._token_factory = token_factory or (lambda: token_urlsafe(32))
        self._records: dict[str, _LeaseRecord] = {}
        self._counter = 0

    @staticmethod
    def _hash(token: str) -> str:
        return sha256(token.encode("utf-8")).hexdigest()

    def issue(
        self,
        *,
        task_id: str,
        operation_id: str,
        principal: str,
        scope: Mapping[str, Any],
        ttl_seconds: float,
    ) -> IssuedLease:
        if not task_id.strip():
            raise ValueError("task_id must be non-empty")
        if not operation_id.strip():
            raise ValueError("operation_id must be non-empty")
        if not principal.strip():
            raise ValueError("principal must be non-empty")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")

        token = self._token_factory()
        if not token:
            raise ValueError("token factory returned an empty token")
        token_hash = self._hash(token)
        if token_hash in self._records:
            raise RuntimeError("token factory produced a duplicate token")

        now = float(self._clock())
        self._counter += 1
        lease = ActionLease(
            lease_id=f"lease-{self._counter}",
            task_id=task_id,
            operation_id=operation_id,
            principal=principal,
            scope=dict(scope),
            issued_at=now,
            expires_at=now + float(ttl_seconds),
        )
        self._records[token_hash] = _LeaseRecord(lease=lease, token_hash=token_hash)
        return IssuedLease(token=token, lease=lease)

    def validate(self, token: str | None, *, operation_id: str) -> ActionLease:
        if not token:
            raise LeaseDenied("missing_action_lease", "No ORION Action Lease was supplied.")

        record = self._records.get(self._hash(token))
        if record is None:
            raise LeaseDenied("unknown_action_lease", "The ORION Action Lease is unknown.")
        if record.revoked:
            raise LeaseDenied("revoked_action_lease", "The ORION Action Lease was revoked.")

        now = float(self._clock())
        if now >= record.lease.expires_at:
            raise LeaseDenied("expired_action_lease", "The ORION Action Lease expired.")
        if record.lease.operation_id != operation_id:
            raise LeaseDenied(
                "wrong_operation",
                "The ORION Action Lease does not authorize this operation.",
            )
        return record.lease

    def revoke(self, token: str) -> None:
        record = self._records.get(self._hash(token))
        if record is None:
            raise LeaseDenied("unknown_action_lease", "The ORION Action Lease is unknown.")
        record.revoked = True