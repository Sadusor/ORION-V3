from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4

from orion_v3.capabilities import (
    ApprovalClass,
    CapabilityProposal,
    CapabilityRegistry,
    inherited_registry_v0,
)
from orion_v3.state import EventType, LocalEventExchange, OrionStateStore, StateStoreError


class OperatorControlDenied(StateStoreError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"
    CONSUMED = "CONSUMED"


@dataclass(frozen=True)
class FrozenCapabilityAction:
    capability_id: str
    capability_version: int
    params: Mapping[str, Any]
    action_sha256: str


@dataclass(frozen=True)
class ApprovalRecord:
    approval_id: str
    project_id: str
    task_id: str
    action: FrozenCapabilityAction
    approval_class: ApprovalClass
    status: ApprovalStatus
    requested_by: str
    requested_event_id: str
    decided_by: str | None
    decision_event_id: str | None
    consumed_by: str | None
    consumed_event_id: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class CapabilityActionProposal:
    project_id: str
    task_id: str
    action: FrozenCapabilityAction
    approval_class: ApprovalClass
    event_id: str
    proposed_by: str


@dataclass(frozen=True)
class ApprovalRequestResult:
    approval: ApprovalRecord
    duplicate: bool


@dataclass(frozen=True)
class ApprovalDecisionResult:
    approval: ApprovalRecord
    duplicate: bool


@dataclass(frozen=True)
class ConsumedApproval:
    approval: ApprovalRecord
    action: FrozenCapabilityAction


@dataclass(frozen=True)
class CloudRequestRecord:
    request_id: str
    project_id: str
    task_id: str
    specialty: str
    task: str
    request_sha256: str
    recipient: str
    event_id: str
    requested_by: str
    created_at: str


@dataclass(frozen=True)
class CloudQueueResult:
    request: CloudRequestRecord
    duplicate: bool


@dataclass(frozen=True)
class CloudResponseResult:
    request: CloudRequestRecord
    event_id: str
    response_sha256: str
    duplicate: bool


_OPERATOR_SCHEMA = """
CREATE TABLE IF NOT EXISTS operator_approvals (
    approval_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    task_id TEXT NOT NULL REFERENCES tasks(task_id),
    action_sha256 TEXT NOT NULL,
    action_json TEXT NOT NULL,
    approval_class INTEGER NOT NULL,
    status TEXT NOT NULL,
    requested_by TEXT NOT NULL,
    requested_event_id TEXT NOT NULL REFERENCES events(event_id),
    decided_by TEXT,
    decision_event_id TEXT REFERENCES events(event_id),
    consumed_by TEXT,
    consumed_event_id TEXT REFERENCES events(event_id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_operator_approvals_task
    ON operator_approvals(task_id, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_operator_one_live_exact_approval
    ON operator_approvals(task_id, action_sha256)
    WHERE status IN ('PENDING', 'APPROVED');

CREATE TABLE IF NOT EXISTS operator_cloud_requests (
    request_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    task_id TEXT NOT NULL REFERENCES tasks(task_id),
    specialty TEXT NOT NULL,
    task_text TEXT NOT NULL,
    request_sha256 TEXT NOT NULL,
    recipient TEXT NOT NULL,
    event_id TEXT NOT NULL REFERENCES events(event_id),
    requested_by TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_operator_cloud_request_dedupe
    ON operator_cloud_requests(task_id, request_sha256);
"""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


class OperatorControlPlane:
    """Deterministic authority/state layer underneath the local ORION operator.

    The model may request an approval or a cloud specialist, but it never owns
    approval state, action identity, replay semantics, or cloud dispatch truth.
    """

    CLOUD_SPECIALTIES = frozenset({"architecture", "coding", "review"})

    def __init__(
        self,
        store: OrionStateStore,
        *,
        registry: CapabilityRegistry | None = None,
    ) -> None:
        self.store = store
        self.registry = registry or inherited_registry_v0()

    def initialize(self) -> None:
        self.store.connect().executescript(_OPERATOR_SCHEMA)
        self.store.connect().commit()

    def propose_capability_action(
        self,
        task_id: str,
        *,
        capability_id: str,
        params: Mapping[str, Any],
        proposed_by: str,
        parent_event_id: str | None = None,
    ) -> CapabilityActionProposal:
        """Validate and freeze one non-approval capability proposal.

        This records intent only. It does not execute a Hand and does not mint
        execution authority. Bounded/consequential capabilities must use the
        explicit approval lane instead.
        """
        task = self._require_task(task_id)
        proposed_by = self._required_text(proposed_by, "proposed_by")

        resolved = self.registry.resolve(
            CapabilityProposal(intent=capability_id, params=dict(params))
        )
        definition = resolved.definition
        if definition.approval_class.value >= ApprovalClass.BOUNDED_MODIFICATION.value:
            raise OperatorControlDenied(
                "approval_required",
                "This capability requires the explicit approval lane.",
            )

        action_payload = {
            "capability_id": definition.capability_id,
            "capability_version": definition.version,
            "params": dict(resolved.params),
        }
        action_sha = _sha256(action_payload)
        event = self.store.append_event(
            task.project_id,
            EventType.PROPOSAL,
            {
                "operator_control_version": 1,
                "kind": "capability_action_proposed",
                "action_sha256": action_sha,
                "action": action_payload,
            },
            actor_kind="local_operator",
            actor_id=proposed_by,
            task_id=task_id,
            parent_event_id=parent_event_id,
        )
        return CapabilityActionProposal(
            project_id=task.project_id,
            task_id=task_id,
            action=FrozenCapabilityAction(
                capability_id=definition.capability_id,
                capability_version=definition.version,
                params=dict(resolved.params),
                action_sha256=action_sha,
            ),
            approval_class=definition.approval_class,
            event_id=event.event_id,
            proposed_by=proposed_by,
        )

    def request_approval(
        self,
        task_id: str,
        *,
        capability_id: str,
        params: Mapping[str, Any],
        requested_by: str,
    ) -> ApprovalRequestResult:
        task = self._require_task(task_id)
        requested_by = self._required_text(requested_by, "requested_by")

        definition = self.registry.get(capability_id)
        normalized = definition.normalize_params(params)
        if definition.approval_class.value < ApprovalClass.BOUNDED_MODIFICATION.value:
            raise OperatorControlDenied(
                "approval_not_required",
                "This capability does not require explicit bounded-modification approval.",
            )

        action_payload = {
            "capability_id": definition.capability_id,
            "capability_version": definition.version,
            "params": normalized,
        }
        action_sha = _sha256(action_payload)
        action_json = _canonical_json(action_payload)
        now = _utc_now()
        conn = self.store.connect()

        try:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute(
                """
                SELECT * FROM operator_approvals
                WHERE task_id=? AND action_sha256=? AND status IN ('PENDING','APPROVED')
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (task_id, action_sha),
            ).fetchone()
            if existing is not None:
                conn.commit()
                return ApprovalRequestResult(
                    approval=self._row_to_approval(existing),
                    duplicate=True,
                )

            event = self.store.append_event(
                task.project_id,
                EventType.PROPOSAL,
                {
                    "operator_control_version": 1,
                    "kind": "approval_request",
                    "action_sha256": action_sha,
                    "action": action_payload,
                },
                actor_kind="local_operator",
                actor_id=requested_by,
                task_id=task_id,
                commit=False,
            )

            approval_id = str(uuid4())
            conn.execute(
                """
                INSERT INTO operator_approvals(
                    approval_id,project_id,task_id,action_sha256,action_json,
                    approval_class,status,requested_by,requested_event_id,
                    created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    approval_id,
                    task.project_id,
                    task_id,
                    action_sha,
                    action_json,
                    int(definition.approval_class.value),
                    ApprovalStatus.PENDING.value,
                    requested_by,
                    event.event_id,
                    now,
                    now,
                ),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.rollback()
            existing = conn.execute(
                """
                SELECT * FROM operator_approvals
                WHERE task_id=? AND action_sha256=? AND status IN ('PENDING','APPROVED')
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (task_id, action_sha),
            ).fetchone()
            if existing is None:
                raise
            return ApprovalRequestResult(
                approval=self._row_to_approval(existing),
                duplicate=True,
            )
        except Exception:
            conn.rollback()
            raise

        return ApprovalRequestResult(
            approval=self.get_approval(approval_id),
            duplicate=False,
        )

    def approve(
        self,
        approval_id: str,
        *,
        approved_by: str,
    ) -> ApprovalDecisionResult:
        approved_by = self._required_text(approved_by, "approved_by")
        conn = self.store.connect()

        try:
            conn.execute("BEGIN IMMEDIATE")
            row = self._approval_row(approval_id)
            status = ApprovalStatus(row["status"])

            if status == ApprovalStatus.APPROVED:
                conn.commit()
                return ApprovalDecisionResult(
                    approval=self._row_to_approval(row),
                    duplicate=True,
                )
            if status == ApprovalStatus.CONSUMED:
                raise OperatorControlDenied(
                    "stale_approval",
                    "This approval has already been consumed.",
                )
            if status == ApprovalStatus.REJECTED:
                raise OperatorControlDenied(
                    "approval_rejected",
                    "This approval was rejected and cannot be approved later.",
                )
            if status == ApprovalStatus.REVOKED:
                raise OperatorControlDenied(
                    "approval_revoked",
                    "This approval was revoked and cannot be approved later.",
                )

            event = self.store.append_event(
                row["project_id"],
                EventType.DECISION,
                {
                    "operator_control_version": 1,
                    "kind": "approval_decision",
                    "approval_id": approval_id,
                    "decision": "APPROVED",
                    "action_sha256": row["action_sha256"],
                },
                actor_kind="human",
                actor_id=approved_by,
                task_id=row["task_id"],
                parent_event_id=row["requested_event_id"],
                commit=False,
            )
            now = _utc_now()
            conn.execute(
                """
                UPDATE operator_approvals
                SET status='APPROVED',decided_by=?,decision_event_id=?,updated_at=?
                WHERE approval_id=?
                """,
                (approved_by, event.event_id, now, approval_id),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise

        return ApprovalDecisionResult(
            approval=self.get_approval(approval_id),
            duplicate=False,
        )

    def reject(
        self,
        approval_id: str,
        *,
        rejected_by: str,
        reason: str,
    ) -> ApprovalDecisionResult:
        rejected_by = self._required_text(rejected_by, "rejected_by")
        reason = self._required_text(reason, "reason")
        conn = self.store.connect()

        try:
            conn.execute("BEGIN IMMEDIATE")
            row = self._approval_row(approval_id)
            status = ApprovalStatus(row["status"])

            if status == ApprovalStatus.REJECTED:
                conn.commit()
                return ApprovalDecisionResult(
                    approval=self._row_to_approval(row),
                    duplicate=True,
                )
            if status == ApprovalStatus.CONSUMED:
                raise OperatorControlDenied(
                    "stale_approval",
                    "Consumed approval cannot be rejected.",
                )
            if status == ApprovalStatus.APPROVED:
                raise OperatorControlDenied(
                    "approval_already_granted",
                    "Use revoke() to cancel an already-approved action.",
                )

            event = self.store.append_event(
                row["project_id"],
                EventType.DECISION,
                {
                    "operator_control_version": 1,
                    "kind": "approval_decision",
                    "approval_id": approval_id,
                    "decision": "REJECTED",
                    "reason": reason,
                    "action_sha256": row["action_sha256"],
                },
                actor_kind="human",
                actor_id=rejected_by,
                task_id=row["task_id"],
                parent_event_id=row["requested_event_id"],
                commit=False,
            )
            now = _utc_now()
            conn.execute(
                """
                UPDATE operator_approvals
                SET status='REJECTED',decided_by=?,decision_event_id=?,updated_at=?
                WHERE approval_id=?
                """,
                (rejected_by, event.event_id, now, approval_id),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise

        return ApprovalDecisionResult(
            approval=self.get_approval(approval_id),
            duplicate=False,
        )

    def revoke(
        self,
        approval_id: str,
        *,
        revoked_by: str,
        reason: str,
    ) -> ApprovalDecisionResult:
        revoked_by = self._required_text(revoked_by, "revoked_by")
        reason = self._required_text(reason, "reason")
        conn = self.store.connect()

        try:
            conn.execute("BEGIN IMMEDIATE")
            row = self._approval_row(approval_id)
            status = ApprovalStatus(row["status"])

            if status == ApprovalStatus.REVOKED:
                conn.commit()
                return ApprovalDecisionResult(
                    approval=self._row_to_approval(row),
                    duplicate=True,
                )
            if status == ApprovalStatus.CONSUMED:
                raise OperatorControlDenied(
                    "stale_approval",
                    "Consumed approval cannot be revoked.",
                )
            if status == ApprovalStatus.REJECTED:
                raise OperatorControlDenied(
                    "approval_rejected",
                    "Rejected approval cannot be revoked.",
                )
            if status == ApprovalStatus.PENDING:
                raise OperatorControlDenied(
                    "approval_not_granted",
                    "Pending approval must be rejected, not revoked.",
                )
            if not row["decision_event_id"]:
                raise OperatorControlDenied(
                    "approval_state_corrupt",
                    "Approved action has no decision event.",
                )

            event = self.store.append_event(
                row["project_id"],
                EventType.DECISION,
                {
                    "operator_control_version": 1,
                    "kind": "approval_revoked",
                    "approval_id": approval_id,
                    "decision": "REVOKED",
                    "reason": reason,
                    "action_sha256": row["action_sha256"],
                },
                actor_kind="human",
                actor_id=revoked_by,
                task_id=row["task_id"],
                parent_event_id=row["decision_event_id"],
                commit=False,
            )
            now = _utc_now()
            conn.execute(
                """
                UPDATE operator_approvals
                SET status='REVOKED',decided_by=?,decision_event_id=?,updated_at=?
                WHERE approval_id=? AND status='APPROVED'
                """,
                (revoked_by, event.event_id, now, approval_id),
            )
            if conn.execute("SELECT changes()").fetchone()[0] != 1:
                raise OperatorControlDenied(
                    "stale_approval",
                    "Approval changed before revocation completed.",
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise

        return ApprovalDecisionResult(
            approval=self.get_approval(approval_id),
            duplicate=False,
        )

    def consume_approved_action(
        self,
        approval_id: str,
        *,
        task_id: str,
        consumed_by: str,
    ) -> ConsumedApproval:
        consumed_by = self._required_text(consumed_by, "consumed_by")
        conn = self.store.connect()

        try:
            conn.execute("BEGIN IMMEDIATE")
            row = self._approval_row(approval_id)
            if row["task_id"] != task_id:
                raise OperatorControlDenied(
                    "wrong_task",
                    "Approval belongs to a different task.",
                )

            status = ApprovalStatus(row["status"])
            if status == ApprovalStatus.PENDING:
                raise OperatorControlDenied(
                    "approval_pending",
                    "Approval is still pending.",
                )
            if status == ApprovalStatus.REJECTED:
                raise OperatorControlDenied(
                    "approval_rejected",
                    "Rejected approval cannot be consumed.",
                )
            if status == ApprovalStatus.REVOKED:
                raise OperatorControlDenied(
                    "approval_revoked",
                    "Revoked approval cannot be consumed.",
                )
            if status == ApprovalStatus.CONSUMED:
                raise OperatorControlDenied(
                    "stale_approval",
                    "Approval has already been consumed.",
                )
            if not row["decision_event_id"]:
                raise OperatorControlDenied(
                    "approval_state_corrupt",
                    "Approved action has no decision event.",
                )

            action_payload = json.loads(row["action_json"])
            if _sha256(action_payload) != row["action_sha256"]:
                raise OperatorControlDenied(
                    "approval_tamper_detected",
                    "Frozen approved action failed its content hash.",
                )

            event = self.store.append_event(
                row["project_id"],
                EventType.ACTION,
                {
                    "operator_control_version": 1,
                    "kind": "approved_action_consumed",
                    "approval_id": approval_id,
                    "action_sha256": row["action_sha256"],
                    "action": action_payload,
                },
                actor_kind="orion",
                actor_id=consumed_by,
                task_id=task_id,
                parent_event_id=row["decision_event_id"],
                commit=False,
            )
            now = _utc_now()
            conn.execute(
                """
                UPDATE operator_approvals
                SET status='CONSUMED',consumed_by=?,consumed_event_id=?,updated_at=?
                WHERE approval_id=? AND status='APPROVED'
                """,
                (consumed_by, event.event_id, now, approval_id),
            )
            if conn.execute("SELECT changes()").fetchone()[0] != 1:
                raise OperatorControlDenied(
                    "stale_approval",
                    "Approval was consumed concurrently.",
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise

        approval = self.get_approval(approval_id)
        return ConsumedApproval(
            approval=approval,
            action=approval.action,
        )

    def queue_cloud_specialist(
        self,
        task_id: str,
        *,
        specialty: str,
        task: str,
        requested_by: str,
        parent_event_id: str | None = None,
    ) -> CloudQueueResult:
        task_record = self._require_task(task_id)
        specialty = self._required_text(specialty, "specialty").lower()
        if specialty not in self.CLOUD_SPECIALTIES:
            raise OperatorControlDenied(
                "invalid_cloud_specialty",
                "Cloud specialty must be architecture, coding, or review.",
            )
        task_text = self._required_text(task, "task")
        requested_by = self._required_text(requested_by, "requested_by")

        request_body = {
            "operator_control_version": 1,
            "kind": "cloud_specialist_request",
            "specialty": specialty,
            "task": task_text,
        }
        request_sha = _sha256(request_body)
        recipient = "cloud:" + specialty
        now = _utc_now()
        conn = self.store.connect()

        try:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute(
                """
                SELECT * FROM operator_cloud_requests
                WHERE task_id=? AND request_sha256=?
                """,
                (task_id, request_sha),
            ).fetchone()
            if existing is not None:
                conn.commit()
                return CloudQueueResult(
                    request=self._row_to_cloud_request(existing),
                    duplicate=True,
                )

            event = self.store.append_event(
                task_record.project_id,
                EventType.PROPOSAL,
                {
                    "exchange_version": 1,
                    "recipient": recipient,
                    "body": {
                        **request_body,
                        "request_sha256": request_sha,
                    },
                },
                actor_kind="local_operator",
                actor_id=requested_by,
                task_id=task_id,
                parent_event_id=parent_event_id,
                commit=False,
            )

            request_id = str(uuid4())
            conn.execute(
                """
                INSERT INTO operator_cloud_requests(
                    request_id,project_id,task_id,specialty,task_text,
                    request_sha256,recipient,event_id,requested_by,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    request_id,
                    task_record.project_id,
                    task_id,
                    specialty,
                    task_text,
                    request_sha,
                    recipient,
                    event.event_id,
                    requested_by,
                    now,
                ),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.rollback()
            existing = conn.execute(
                """
                SELECT * FROM operator_cloud_requests
                WHERE task_id=? AND request_sha256=?
                """,
                (task_id, request_sha),
            ).fetchone()
            if existing is None:
                raise
            return CloudQueueResult(
                request=self._row_to_cloud_request(existing),
                duplicate=True,
            )
        except Exception:
            conn.rollback()
            raise

        return CloudQueueResult(
            request=self.get_cloud_request(request_id),
            duplicate=False,
        )

    def ingest_cloud_specialist_response(
        self,
        request_id: str,
        *,
        source_system: str,
        external_message_id: str,
        provider_id: str,
        model_id: str,
        response_text: str,
    ) -> CloudResponseResult:
        """Bind one external specialist response to an exact queued request.

        The response is immutable advisory REVIEW evidence. It does not approve,
        execute, consume authority, or mutate the original cloud request.
        """
        request = self.get_cloud_request(request_id)
        source_system = self._required_text(source_system, "source_system")
        external_message_id = self._required_text(
            external_message_id,
            "external_message_id",
        )
        provider_id = self._required_text(provider_id, "provider_id")
        model_id = self._required_text(model_id, "model_id")
        response_text = str(response_text)
        if not response_text.strip():
            raise OperatorControlDenied(
                "invalid_argument",
                "response_text must be non-empty.",
            )
        if len(response_text) > 2_000_000:
            raise OperatorControlDenied(
                "invalid_argument",
                "response_text exceeds maximum length.",
            )

        response_payload = {
            "operator_control_version": 1,
            "kind": "cloud_specialist_response",
            "request_id": request.request_id,
            "request_sha256": request.request_sha256,
            "specialty": request.specialty,
            "provider_id": provider_id,
            "model_id": model_id,
            "response_text": response_text,
            "authority": "advisory_only",
        }
        response_sha = _sha256(response_payload)
        body = {
            **response_payload,
            "response_sha256": response_sha,
        }

        exchange = LocalEventExchange(self.store)
        published = exchange.ingest_external(
            request.project_id,
            request.task_id,
            EventType.REVIEW,
            source_system=source_system,
            external_message_id=external_message_id,
            actor_kind="cloud_specialist",
            actor_id=provider_id + ":" + model_id,
            recipient="orion:governor",
            body=body,
            parent_event_id=request.event_id,
        )
        return CloudResponseResult(
            request=request,
            event_id=published.event.event_id,
            response_sha256=response_sha,
            duplicate=published.duplicate,
        )

    def get_approval(self, approval_id: str) -> ApprovalRecord:
        return self._row_to_approval(self._approval_row(approval_id))

    def get_cloud_request(self, request_id: str) -> CloudRequestRecord:
        row = self.store.connect().execute(
            "SELECT * FROM operator_cloud_requests WHERE request_id=?",
            (request_id,),
        ).fetchone()
        if row is None:
            raise OperatorControlDenied(
                "unknown_cloud_request",
                "Cloud request does not exist.",
            )
        return self._row_to_cloud_request(row)

    def _approval_row(self, approval_id: str) -> sqlite3.Row:
        row = self.store.connect().execute(
            "SELECT * FROM operator_approvals WHERE approval_id=?",
            (approval_id,),
        ).fetchone()
        if row is None:
            raise OperatorControlDenied(
                "unknown_approval",
                "Approval does not exist.",
            )
        return row

    def _require_task(self, task_id: str):
        task = self.store.get_task(task_id)
        if task is None:
            raise OperatorControlDenied(
                "unknown_task",
                "Task does not exist.",
            )
        return task

    @staticmethod
    def _required_text(value: str, field: str) -> str:
        value = str(value or "").strip()
        if not value:
            raise OperatorControlDenied(
                "invalid_argument",
                field + " must be non-empty.",
            )
        return value

    @staticmethod
    def _row_to_approval(row: sqlite3.Row) -> ApprovalRecord:
        action_payload = json.loads(row["action_json"])
        action = FrozenCapabilityAction(
            capability_id=action_payload["capability_id"],
            capability_version=int(action_payload["capability_version"]),
            params=dict(action_payload["params"]),
            action_sha256=row["action_sha256"],
        )
        return ApprovalRecord(
            approval_id=row["approval_id"],
            project_id=row["project_id"],
            task_id=row["task_id"],
            action=action,
            approval_class=ApprovalClass(int(row["approval_class"])),
            status=ApprovalStatus(row["status"]),
            requested_by=row["requested_by"],
            requested_event_id=row["requested_event_id"],
            decided_by=row["decided_by"],
            decision_event_id=row["decision_event_id"],
            consumed_by=row["consumed_by"],
            consumed_event_id=row["consumed_event_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_cloud_request(row: sqlite3.Row) -> CloudRequestRecord:
        return CloudRequestRecord(
            request_id=row["request_id"],
            project_id=row["project_id"],
            task_id=row["task_id"],
            specialty=row["specialty"],
            task=row["task_text"],
            request_sha256=row["request_sha256"],
            recipient=row["recipient"],
            event_id=row["event_id"],
            requested_by=row["requested_by"],
            created_at=row["created_at"],
        )


__all__ = [
    "ApprovalDecisionResult",
    "ApprovalRecord",
    "ApprovalRequestResult",
    "ApprovalStatus",
    "CloudQueueResult",
    "CloudRequestRecord",
    "CloudResponseResult",
    "ConsumedApproval",
    "FrozenCapabilityAction",
    "OperatorControlDenied",
    "OperatorControlPlane",
]
