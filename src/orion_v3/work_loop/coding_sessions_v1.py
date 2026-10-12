"""Isolated in-memory coding-session lifecycle; no IO or model dispatch.

The caller owns persistence, identity authentication and policy enforcement.
This adapter only separates main/coding conversation identities and tracks
trusted role-contract hashes across task revisions.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .role_contracts_v1 import Role, RolePrompt, TrustedBindings, assemble_role_prompt


class SessionState(StrEnum):
    ACTIVE = "active"
    STALE = "stale"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class SessionRecord:
    session_id: str
    role: Role
    project_id: str | None
    task_id: str | None
    contract_hash: str
    state: SessionState


class CodingSessionRegistry:
    """In-memory deterministic lifecycle. NOT an authority or durable store."""

    def __init__(self) -> None:
        self._records: dict[str, SessionRecord] = {}

    def open(
        self,
        role: Role,
        session_id: str,
        bindings: TrustedBindings | None = None,
    ) -> RolePrompt:
        if session_id in self._records:
            raise ValueError("session identity already exists")
        prompt = assemble_role_prompt(role, session_id, bindings)
        self._records[session_id] = SessionRecord(
            session_id=session_id,
            role=prompt.role,
            project_id=bindings.project_id if bindings else None,
            task_id=bindings.task_id if bindings else None,
            contract_hash=prompt.contract_hash,
            state=SessionState.ACTIVE,
        )
        return prompt

    def validate(self, prompt: RolePrompt, bindings: TrustedBindings | None = None) -> bool:
        record = self._records.get(prompt.session_id)
        if record is None or record.state != SessionState.ACTIVE:
            return False
        if record.role != prompt.role or record.contract_hash != prompt.contract_hash:
            return False
        if record.project_id != (bindings.project_id if bindings else None):
            return False
        if record.task_id != (bindings.task_id if bindings else None):
            return False
        try:
            expected = assemble_role_prompt(record.role, record.session_id, bindings)
        except (ValueError, TypeError):
            return False
        return expected.contract_hash == prompt.contract_hash

    def stale_task(self, project_id: str, task_id: str) -> int:
        count = 0
        for session_id, record in tuple(self._records.items()):
            if record.project_id == project_id and record.task_id == task_id and record.state == SessionState.ACTIVE:
                self._records[session_id] = SessionRecord(
                    record.session_id, record.role, record.project_id, record.task_id,
                    record.contract_hash, SessionState.STALE,
                )
                count += 1
        return count

    def close(self, session_id: str) -> None:
        record = self._records[session_id]
        self._records[session_id] = SessionRecord(
            record.session_id, record.role, record.project_id, record.task_id,
            record.contract_hash, SessionState.CLOSED,
        )

    def snapshot(self) -> tuple[SessionRecord, ...]:
        return tuple(self._records.values())
