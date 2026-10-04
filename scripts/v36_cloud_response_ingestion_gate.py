from __future__ import annotations

import json
import tempfile
from pathlib import Path

from orion_v3.operator import OperatorControlPlane
from orion_v3.state import EventType, LocalEventExchange, OrionStateStore, StateStoreError


def main() -> int:
    print("V3_RUN_ID> V3-RUN-046")
    print("ORION_CLOUD_RESPONSE_INGESTION> START")
    print("MODE> deterministic advisory-return gate; no model; no network; no Hand")

    with tempfile.TemporaryDirectory(prefix="orion-run046-") as td:
        db = Path(td) / "orion.db"
        store = OrionStateStore(db)
        store.initialize()
        project = store.create_project("RUN-046", project_id="run046-project")
        task = store.create_task(
            project.project_id,
            "Route and receive one coding-specialist review",
            task_id="run046-task",
        )
        control = OperatorControlPlane(store)
        control.initialize()
        exchange = LocalEventExchange(store)

        queued = control.queue_cloud_specialist(
            task.task_id,
            specialty="coding",
            task="Refactor a bounded parser module and return an advisory implementation review.",
            requested_by="qwen35-9b-orion",
        )
        request = queued.request
        print("CLOUD_REQUEST_QUEUED> PASS " + request.request_id)
        print("CLOUD_REQUEST_EVENT> " + request.event_id)
        print("CLOUD_REQUEST_SHA256> " + request.request_sha256)

        response_text = (
            "Advisory coding response fixture for RUN-046. "
            "This text may recommend implementation steps but has no approval "
            "or execution authority."
        )
        first = control.ingest_cloud_specialist_response(
            request.request_id,
            source_system="run046-fixture-provider",
            external_message_id="run046-message-1",
            provider_id="fixture-provider",
            model_id="fixture-coder",
            response_text=response_text,
        )
        print("CLOUD_RESPONSE_INGESTED> PASS " + first.event_id)
        print("CLOUD_RESPONSE_SHA256> " + first.response_sha256)

        event = store.get_event(first.event_id)
        if event is None:
            raise RuntimeError("response event missing")
        if event.event_type != EventType.REVIEW:
            raise RuntimeError("cloud response is not REVIEW")
        if event.parent_event_id != request.event_id:
            raise RuntimeError("cloud response is not bound to exact request event")
        body = event.payload.get("body") or {}
        if body.get("request_id") != request.request_id:
            raise RuntimeError("response request_id mismatch")
        if body.get("request_sha256") != request.request_sha256:
            raise RuntimeError("response request hash mismatch")
        if body.get("authority") != "advisory_only":
            raise RuntimeError("cloud response gained authority")
        if body.get("response_text") != response_text:
            raise RuntimeError("response text changed during ingestion")
        print("REQUEST_RESPONSE_BINDING> PASS")
        print("RESPONSE_EVENT_TYPE_REVIEW> PASS")
        print("RESPONSE_AUTHORITY_ADVISORY_ONLY> PASS")

        duplicate = control.ingest_cloud_specialist_response(
            request.request_id,
            source_system="run046-fixture-provider",
            external_message_id="run046-message-1",
            provider_id="fixture-provider",
            model_id="fixture-coder",
            response_text=response_text,
        )
        if not duplicate.duplicate or duplicate.event_id != first.event_id:
            raise RuntimeError("exact external duplicate was not idempotent")
        print("EXACT_EXTERNAL_DUPLICATE> PASS")

        collision_blocked = False
        try:
            control.ingest_cloud_specialist_response(
                request.request_id,
                source_system="run046-fixture-provider",
                external_message_id="run046-message-1",
                provider_id="fixture-provider",
                model_id="fixture-coder",
                response_text="Different immutable content under same provider message id.",
            )
        except StateStoreError:
            collision_blocked = True
        if not collision_blocked:
            raise RuntimeError("external message collision did not fail closed")
        print("EXTERNAL_ID_COLLISION> BLOCKED")

        inbox = exchange.inbox(
            task.project_id,
            task.task_id,
            "orion:governor",
        )
        if len(inbox) != 1 or inbox[0].event_id != first.event_id:
            raise RuntimeError("governor inbox did not contain exact response once")
        if inbox[0].event_type != EventType.REVIEW:
            raise RuntimeError("governor inbox response changed event type")
        print("GOVERNOR_INBOX_RESPONSE> PASS")

        events = store.list_task_events(task.project_id, task.task_id)
        event_types = [item.event_type for item in events]
        if event_types != [EventType.PROPOSAL, EventType.REVIEW]:
            raise RuntimeError("unexpected authority-bearing event appeared: " + repr(event_types))
        if any(
            item.event_type in {EventType.DECISION, EventType.ACTION}
            for item in events
        ):
            raise RuntimeError("cloud response created DECISION/ACTION authority")
        print("CLOUD_RESPONSE_DECISIONS_CREATED> 0")
        print("CLOUD_RESPONSE_ACTIONS_CREATED> 0")
        print("HAND_EXECUTIONS> 0")
        print("EXTERNAL_PROVIDER_CALLS> 0")

        response_event_id = first.event_id
        store.close()

        reopened = OrionStateStore(db)
        reopened.initialize()
        persisted = reopened.get_event(response_event_id)
        if persisted is None:
            raise RuntimeError("response did not survive restart")
        if persisted.parent_event_id != request.event_id:
            raise RuntimeError("request-response lineage changed after restart")
        if persisted.payload["body"].get("authority") != "advisory_only":
            raise RuntimeError("response authority changed after restart")
        reopened.close()
        print("RESTART_PERSISTENCE> PASS")

        summary = {
            "schema": "orion.v3.cloud-specialist-response-ingestion.v0",
            "run_id": "V3-RUN-046",
            "request_id": request.request_id,
            "request_event_id": request.event_id,
            "request_sha256": request.request_sha256,
            "response_event_id": response_event_id,
            "response_sha256": first.response_sha256,
            "event_type": "REVIEW",
            "authority": "advisory_only",
            "exact_duplicate_idempotent": True,
            "collision_fail_closed": True,
            "decisions_created": 0,
            "actions_created": 0,
            "hand_executions": 0,
            "external_provider_calls": 0,
        }
        print(
            "ORION_CLOUD_RESPONSE_SUMMARY> "
            + json.dumps(summary, ensure_ascii=False, sort_keys=True)
        )

    print("ORION_CLOUD_RESPONSE_INGESTION> PASS")
    print("STATUS> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
