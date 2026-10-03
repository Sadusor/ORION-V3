from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any, Mapping
from uuid import UUID, uuid5

from .store import EventRecord, EventType, OrionStateStore, StateStoreError


_EXCHANGE_NAMESPACE = UUID("d4a7c7b1-6f08-45ec-9bca-4fbfc9654f52")
_ALLOWED_EVENT_TYPES = {
    EventType.PROPOSAL,
    EventType.REVIEW,
    EventType.DECISION,
    EventType.ACTION,
    EventType.EVIDENCE,
    EventType.RESULT,
    EventType.FAILURE,
}


@dataclass(frozen=True)
class ExchangePublishResult:
    event: EventRecord
    duplicate: bool


@dataclass(frozen=True)
class ExchangeMessage:
    event_id: str
    project_id: str
    task_id: str
    event_type: EventType
    actor_kind: str
    actor_id: str
    recipient: str
    body: Mapping[str, Any]
    created_at: str
    parent_event_id: str | None
    acknowledged: bool


class LocalEventExchange:
    """Append-only local AI/ORION/Hand exchange built on the Event Ledger."""

    def __init__(self, store: OrionStateStore) -> None:
        self.store = store

    def publish(
        self,
        project_id: str,
        task_id: str,
        event_type: EventType,
        *,
        actor_kind: str,
        actor_id: str,
        recipient: str,
        body: Mapping[str, Any],
        parent_event_id: str | None = None,
        attempt_id: str | None = None,
    ) -> ExchangePublishResult:
        self._validate_type(event_type)
        recipient = self._validate_recipient(recipient)
        payload = self._payload(recipient, body)
        event = self.store.append_event(
            project_id,
            event_type,
            payload,
            actor_kind=actor_kind,
            actor_id=actor_id,
            task_id=task_id,
            attempt_id=attempt_id,
            parent_event_id=parent_event_id,
        )
        return ExchangePublishResult(event=event, duplicate=False)

    def ingest_external(
        self,
        project_id: str,
        task_id: str,
        event_type: EventType,
        *,
        source_system: str,
        external_message_id: str,
        actor_kind: str,
        actor_id: str,
        recipient: str,
        body: Mapping[str, Any],
        parent_event_id: str | None = None,
        attempt_id: str | None = None,
    ) -> ExchangePublishResult:
        self._validate_type(event_type)
        recipient = self._validate_recipient(recipient)
        source_system = source_system.strip()
        external_message_id = external_message_id.strip()
        if not source_system or not external_message_id:
            raise StateStoreError(
                "source_system and external_message_id must be non-empty"
            )

        event_id = str(
            uuid5(
                _EXCHANGE_NAMESPACE,
                project_id + "|" + source_system + "|" + external_message_id,
            )
        )
        payload = self._payload(recipient, body)

        existing = self.store.get_event(event_id)
        if existing is not None:
            self._assert_same_external_message(
                existing,
                project_id=project_id,
                task_id=task_id,
                event_type=event_type,
                actor_kind=actor_kind,
                actor_id=actor_id,
                payload=payload,
                parent_event_id=parent_event_id,
                attempt_id=attempt_id,
            )
            return ExchangePublishResult(event=existing, duplicate=True)

        try:
            event = self.store.append_event(
                project_id,
                event_type,
                payload,
                actor_kind=actor_kind,
                actor_id=actor_id,
                task_id=task_id,
                attempt_id=attempt_id,
                parent_event_id=parent_event_id,
                event_id=event_id,
            )
            return ExchangePublishResult(event=event, duplicate=False)
        except sqlite3.IntegrityError:
            # A concurrent identical ingestion may have won the race.
            existing = self.store.get_event(event_id)
            if existing is None:
                raise
            self._assert_same_external_message(
                existing,
                project_id=project_id,
                task_id=task_id,
                event_type=event_type,
                actor_kind=actor_kind,
                actor_id=actor_id,
                payload=payload,
                parent_event_id=parent_event_id,
                attempt_id=attempt_id,
            )
            return ExchangePublishResult(event=existing, duplicate=True)

    def inbox(
        self,
        project_id: str,
        task_id: str,
        recipient: str,
        *,
        limit: int = 20,
        pending_only: bool = True,
    ) -> list[ExchangeMessage]:
        recipient = self._validate_recipient(recipient)
        if limit < 1 or limit > 100:
            raise StateStoreError("exchange inbox limit must be between 1 and 100")

        # Pull a bounded latest window, then filter by immutable recipient data.
        # A future indexed recipient column can replace this without changing the
        # exchange contract.
        events = self.store.list_task_events(
            project_id,
            task_id,
            limit=100,
        )
        messages: list[ExchangeMessage] = []
        for event in events:
            parsed = self._parse_message(event)
            if parsed is None or parsed.recipient != recipient:
                continue
            acknowledged = self._is_acknowledged(event.event_id, recipient)
            if pending_only and acknowledged:
                continue
            messages.append(
                ExchangeMessage(
                    event_id=parsed.event_id,
                    project_id=parsed.project_id,
                    task_id=parsed.task_id,
                    event_type=parsed.event_type,
                    actor_kind=parsed.actor_kind,
                    actor_id=parsed.actor_id,
                    recipient=parsed.recipient,
                    body=parsed.body,
                    created_at=parsed.created_at,
                    parent_event_id=parsed.parent_event_id,
                    acknowledged=acknowledged,
                )
            )
        return messages[-limit:]

    def acknowledge(
        self,
        project_id: str,
        event_id: str,
        recipient: str,
    ) -> None:
        recipient = self._validate_recipient(recipient)
        event = self.store.get_event(event_id)
        if event is None or event.project_id != project_id:
            raise StateStoreError("exchange event does not belong to project")
        parsed = self._parse_message(event)
        if parsed is None or parsed.recipient != recipient:
            raise StateStoreError("recipient does not match exchange event")

        self.store.connect().execute(
            """
            INSERT OR IGNORE INTO exchange_receipts(
                event_id,recipient,acknowledged_at
            ) VALUES(?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            """,
            (event_id, recipient),
        )
        self.store.connect().commit()

    def task_packet(
        self,
        project_id: str,
        task_id: str,
        *,
        limit: int = 20,
    ) -> dict[str, Any]:
        if limit < 1 or limit > 100:
            raise StateStoreError("exchange packet limit must be between 1 and 100")
        task = self.store.get_task(task_id)
        if task is None or task.project_id != project_id:
            raise StateStoreError("task does not belong to project")

        events = self.store.list_task_events(project_id, task_id, limit=limit)
        return {
            "project_context": self.store.get_l0(project_id),
            "task": {
                "task_id": task.task_id,
                "project_id": task.project_id,
                "objective": task.objective,
                "status": task.status,
                "updated_at": task.updated_at,
            },
            "events": [
                {
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "actor_kind": event.actor_kind,
                    "actor_id": event.actor_id,
                    "created_at": event.created_at,
                    "payload": dict(event.payload),
                    "payload_sha256": event.payload_sha256,
                    "parent_event_id": event.parent_event_id,
                    "attempt_id": event.attempt_id,
                }
                for event in events
            ],
        }

    def _is_acknowledged(self, event_id: str, recipient: str) -> bool:
        row = self.store.connect().execute(
            """
            SELECT 1 FROM exchange_receipts
            WHERE event_id=? AND recipient=?
            """,
            (event_id, recipient),
        ).fetchone()
        return row is not None

    @staticmethod
    def _payload(recipient: str, body: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(body, Mapping):
            raise StateStoreError("exchange body must be an object")
        return {
            "exchange_version": 1,
            "recipient": recipient,
            "body": dict(body),
        }

    @staticmethod
    def _validate_type(event_type: EventType) -> None:
        if event_type not in _ALLOWED_EVENT_TYPES:
            raise StateStoreError(
                "event type is not valid for the live exchange: "
                + event_type.value
            )

    @staticmethod
    def _validate_recipient(recipient: str) -> str:
        recipient = recipient.strip()
        if not recipient or len(recipient) > 128:
            raise StateStoreError("recipient must be 1..128 characters")
        return recipient

    @staticmethod
    def _parse_message(event: EventRecord) -> ExchangeMessage | None:
        payload = event.payload
        if (
            payload.get("exchange_version") != 1
            or not isinstance(payload.get("recipient"), str)
            or not isinstance(payload.get("body"), Mapping)
            or event.task_id is None
        ):
            return None
        return ExchangeMessage(
            event_id=event.event_id,
            project_id=event.project_id,
            task_id=event.task_id,
            event_type=event.event_type,
            actor_kind=event.actor_kind,
            actor_id=event.actor_id,
            recipient=payload["recipient"],
            body=dict(payload["body"]),
            created_at=event.created_at,
            parent_event_id=event.parent_event_id,
            acknowledged=False,
        )

    @staticmethod
    def _assert_same_external_message(
        existing: EventRecord,
        *,
        project_id: str,
        task_id: str,
        event_type: EventType,
        actor_kind: str,
        actor_id: str,
        payload: Mapping[str, Any],
        parent_event_id: str | None,
        attempt_id: str | None,
    ) -> None:
        same = (
            existing.project_id == project_id
            and existing.task_id == task_id
            and existing.event_type == event_type
            and existing.actor_kind == actor_kind.strip()
            and existing.actor_id == actor_id.strip()
            and dict(existing.payload) == dict(payload)
            and existing.parent_event_id == parent_event_id
            and existing.attempt_id == attempt_id
        )
        if not same:
            raise StateStoreError(
                "external message id collision with different immutable content"
            )


__all__ = [
    "ExchangeMessage",
    "ExchangePublishResult",
    "LocalEventExchange",
]
