from __future__ import annotations

import json
import tempfile
from pathlib import Path

from orion_v3.operator import ApprovalStatus, OperatorControlDenied, OperatorControlPlane
from orion_v3.state import EventType, LocalEventExchange, OrionStateStore


def expect_denied(code: str, fn) -> None:
    try:
        fn()
    except OperatorControlDenied as exc:
        if exc.code != code:
            raise RuntimeError(
                f"expected denial {code}, got {exc.code}: {exc}"
            ) from exc
        print(f"DENIAL_{code.upper()}> PASS")
        return
    raise RuntimeError(f"expected denial {code}")


def main() -> int:
    print("V3_RUN_ID> V3-RUN-044")
    print("OPERATOR_CONTROL_PLANE_GATE> START")

    with tempfile.TemporaryDirectory(prefix="orion-run044-") as td:
        db_path = Path(td) / "operator.db"
        store = OrionStateStore(db_path)
        store.initialize()
        project = store.create_project(
            "RUN-044 production operator control plane",
            project_id="run044-project",
        )
        task = store.create_task(
            project.project_id,
            "Prove deterministic operator authority semantics",
            task_id="run044-task",
        )
        other = store.create_task(
            project.project_id,
            "Foreign task",
            task_id="run044-other",
        )

        control = OperatorControlPlane(store)
        control.initialize()

        request = control.request_approval(
            task.task_id,
            capability_id="project.publish_exact_artifact",
            params={
                "artifact_path": "docs/operator-proof.txt",
                "artifact_content": "exact approved bytes\n",
            },
            requested_by="qwen35-9b-orion",
        )
        if request.duplicate:
            raise RuntimeError("first approval request was unexpectedly duplicate")
        print("EXACT_ACTION_FREEZE> PASS")
        print("ACTION_SHA256> " + request.approval.action.action_sha256)

        duplicate = control.request_approval(
            task.task_id,
            capability_id="project.publish_exact_artifact",
            params={
                "artifact_content": "exact approved bytes\n",
                "artifact_path": "docs/operator-proof.txt",
            },
            requested_by="qwen35-9b-orion",
        )
        if (
            not duplicate.duplicate
            or duplicate.approval.approval_id != request.approval.approval_id
        ):
            raise RuntimeError("duplicate approval request was not idempotent")
        print("DUPLICATE_APPROVAL_REQUEST_IDEMPOTENT> PASS")

        expect_denied(
            "approval_pending",
            lambda: control.consume_approved_action(
                request.approval.approval_id,
                task_id=task.task_id,
                consumed_by="orion",
            ),
        )

        decision = control.approve(
            request.approval.approval_id,
            approved_by="owner",
        )
        if decision.approval.status != ApprovalStatus.APPROVED:
            raise RuntimeError("approval did not become APPROVED")
        second_decision = control.approve(
            request.approval.approval_id,
            approved_by="owner",
        )
        if not second_decision.duplicate:
            raise RuntimeError("duplicate human approve was not idempotent")
        print("DUPLICATE_HUMAN_APPROVE_IDEMPOTENT> PASS")

        expect_denied(
            "wrong_task",
            lambda: control.consume_approved_action(
                request.approval.approval_id,
                task_id=other.task_id,
                consumed_by="orion",
            ),
        )

        consumed = control.consume_approved_action(
            request.approval.approval_id,
            task_id=task.task_id,
            consumed_by="orion",
        )
        if consumed.approval.status != ApprovalStatus.CONSUMED:
            raise RuntimeError("approval did not become CONSUMED")
        if consumed.action.params != {
            "artifact_path": "docs/operator-proof.txt",
            "artifact_content": "exact approved bytes\n",
        }:
            raise RuntimeError("resume did not return the exact frozen action")
        print("EXACT_APPROVED_ACTION_RESUME> PASS")
        print("MODEL_REWRITE_ON_RESUME> NONE")

        expect_denied(
            "stale_approval",
            lambda: control.consume_approved_action(
                request.approval.approval_id,
                task_id=task.task_id,
                consumed_by="orion",
            ),
        )
        print("SINGLE_USE_APPROVAL> PASS")

        rejected_req = control.request_approval(
            task.task_id,
            capability_id="project.publish_exact_artifact",
            params={
                "artifact_path": "docs/rejected.txt",
                "artifact_content": "must never execute",
            },
            requested_by="qwen35-9b-orion",
        )
        rejected = control.reject(
            rejected_req.approval.approval_id,
            rejected_by="owner",
            reason="owner rejected this exact action",
        )
        if rejected.approval.status != ApprovalStatus.REJECTED:
            raise RuntimeError("rejected approval did not become REJECTED")
        expect_denied(
            "approval_rejected",
            lambda: control.consume_approved_action(
                rejected_req.approval.approval_id,
                task_id=task.task_id,
                consumed_by="orion",
            ),
        )
        print("REJECTED_ACTION_EXECUTION> DENIED")

        tamper_req = control.request_approval(
            task.task_id,
            capability_id="project.publish_exact_artifact",
            params={
                "artifact_path": "docs/tamper.txt",
                "artifact_content": "approved original",
            },
            requested_by="qwen35-9b-orion",
        )
        control.approve(tamper_req.approval.approval_id, approved_by="owner")
        row = store.connect().execute(
            "SELECT action_json FROM operator_approvals WHERE approval_id=?",
            (tamper_req.approval.approval_id,),
        ).fetchone()
        payload = json.loads(row["action_json"])
        payload["params"]["artifact_content"] = "tampered after approval"
        store.connect().execute(
            "UPDATE operator_approvals SET action_json=? WHERE approval_id=?",
            (
                json.dumps(payload, sort_keys=True, separators=(",", ":")),
                tamper_req.approval.approval_id,
            ),
        )
        store.connect().commit()
        expect_denied(
            "approval_tamper_detected",
            lambda: control.consume_approved_action(
                tamper_req.approval.approval_id,
                task_id=task.task_id,
                consumed_by="orion",
            ),
        )
        print("FROZEN_ACTION_TAMPER_GUARD> PASS")

        cloud = control.queue_cloud_specialist(
            task.task_id,
            specialty="architecture",
            task="Compare two ORION memory backends and return a proposal only.",
            requested_by="qwen35-9b-orion",
        )
        cloud_dup = control.queue_cloud_specialist(
            task.task_id,
            specialty="architecture",
            task="Compare two ORION memory backends and return a proposal only.",
            requested_by="qwen35-9b-orion",
        )
        if (
            cloud.duplicate
            or not cloud_dup.duplicate
            or cloud.request.request_id != cloud_dup.request.request_id
        ):
            raise RuntimeError("cloud queue idempotency failed")

        exchange = LocalEventExchange(store)
        inbox = exchange.inbox(
            project.project_id,
            task.task_id,
            "cloud:architecture",
        )
        if len(inbox) != 1:
            raise RuntimeError("expected one cloud architecture queue event")
        if inbox[0].event_id != cloud.request.event_id:
            raise RuntimeError("cloud queue event identity mismatch")
        print("CLOUD_QUEUE_IDEMPOTENT> PASS")
        print("CLOUD_QUEUE_EVENT_EXCHANGE> PASS")
        print("LIVE_CLOUD_PROVIDER_CALL> NONE")

        events = store.list_task_events(project.project_id, task.task_id, limit=100)
        first_chain = [
            event
            for event in events
            if event.event_id
            in {
                request.approval.requested_event_id,
                decision.approval.decision_event_id,
                consumed.approval.consumed_event_id,
            }
        ]
        if len(first_chain) != 3:
            raise RuntimeError("approval event chain incomplete")
        first_chain.sort(key=lambda e: events.index(e))
        if first_chain[1].parent_event_id != first_chain[0].event_id:
            raise RuntimeError("decision is not causally bound to request")
        if first_chain[2].parent_event_id != first_chain[1].event_id:
            raise RuntimeError("action is not causally bound to decision")
        print("PROPOSAL_DECISION_ACTION_CHAIN> PASS")

        consumed_id = consumed.approval.approval_id
        cloud_id = cloud.request.request_id
        consumed_hash = consumed.action.action_sha256
        cloud_hash = cloud.request.request_sha256
        store.close()

        reopened = OrionStateStore(db_path)
        reopened.initialize()
        control2 = OperatorControlPlane(reopened)
        control2.initialize()
        approval2 = control2.get_approval(consumed_id)
        cloud2 = control2.get_cloud_request(cloud_id)
        if (
            approval2.status != ApprovalStatus.CONSUMED
            or approval2.action.action_sha256 != consumed_hash
            or cloud2.request_sha256 != cloud_hash
        ):
            raise RuntimeError("operator control state did not survive restart")
        print("RESTART_PERSISTENCE> PASS")

        expect_denied(
            "stale_approval",
            lambda: control2.consume_approved_action(
                consumed_id,
                task_id=task.task_id,
                consumed_by="orion-after-restart",
            ),
        )
        print("STALE_REPLAY_AFTER_RESTART> DENIED")

        reopened.close()

    print("MODEL_DEPENDENCY> NONE")
    print("NETWORK_DEPENDENCY> NONE")
    print("EXECUTION_SIDE_EFFECT> NONE")
    print("OPERATOR_CONTROL_PLANE_GATE> PASS")
    print("STATUS> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
