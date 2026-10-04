from __future__ import annotations

import json
import tempfile
from pathlib import Path

from orion_v3.operator import (
    OperatorControlPlane,
    call_openai_compatible_advisory,
    groq_gptoss_120b_spec,
)
from orion_v3.state import EventType, LocalEventExchange, OrionStateStore


def build_prompt(*, request_id: str, request_sha256: str, task_text: str) -> str:
    return f"""ORION V3 BOUNDED CLOUD CODING REVIEW

You are a coding specialist. Your response is advisory evidence only.
You have no tools, filesystem, shell, browser, approval, execution, or task-mutation authority.
Do not claim that any action was executed.
Do not invent additional requirements.

ORION request id: {request_id}
ORION request SHA256: {request_sha256}

CODING TASK
{task_text}

Return exactly these headings:
PLAN
RISKS
TESTS
RECOMMENDATION

Keep the answer concise and under 500 words.
"""


def main() -> int:
    print("V3_RUN_ID> V3-RUN-047")
    print("ORION_LIVE_CLOUD_ROUNDTRIP> START")
    print("PROVIDER> groq")
    print("REQUESTED_MODEL> openai/gpt-oss-120b")
    print("AUTHORITY> advisory_only tools=false hands=false fallback=false")

    with tempfile.TemporaryDirectory(prefix="orion-run047-") as td:
        db = Path(td) / "orion.db"
        store = OrionStateStore(db)
        store.initialize()
        try:
            project = store.create_project("RUN-047", project_id="run047-project")
            task = store.create_task(
                project.project_id,
                "Live bounded cloud coding review",
                task_id="run047-task",
            )
            control = OperatorControlPlane(store)
            control.initialize()
            exchange = LocalEventExchange(store)

            task_text = (
                "Review a proposed Python refactor where approval identity, "
                "single-use resume, and cloud response ingestion are stored in SQLite. "
                "Recommend the smallest test set for idempotency, stale replay denial, "
                "transaction rollback, and restart persistence. Do not write or execute code."
            )
            queued = control.queue_cloud_specialist(
                task.task_id,
                specialty="coding",
                task=task_text,
                requested_by="qwen35-9b-orion",
            )
            request = queued.request
            print("CLOUD_REQUEST_QUEUE> PASS")
            print("REQUEST_ID> " + request.request_id)
            print("REQUEST_SHA256> " + request.request_sha256)

            prompt = build_prompt(
                request_id=request.request_id,
                request_sha256=request.request_sha256,
                task_text=request.task,
            )
            provider = groq_gptoss_120b_spec()
            response = call_openai_compatible_advisory(provider, prompt)

            print("PROVIDER_STATUS> " + response.status)
            print("SERVED_MODEL> " + str(response.served_model))
            print("PROVIDER_LATENCY_SECONDS> " + str(response.elapsed_seconds))
            print("PROMPT_SHA256> " + response.prompt_sha256)
            print("PROVIDER_RESPONSE_SHA256> " + response.response_sha256)
            print("PROVIDER_RESPONSE_CHARS> " + str(len(response.response_text)))

            if response.status != "PASS":
                raise RuntimeError(
                    "live provider call did not PASS: " + response.reason
                )
            if response.served_model != provider.model_id:
                raise RuntimeError("provider model identity mismatch")
            if not response.external_message_id:
                raise RuntimeError("provider response omitted external message id")
            if not response.response_text.strip():
                raise RuntimeError("provider returned empty advisory response")

            ingested = control.ingest_cloud_specialist_response(
                request.request_id,
                source_system="groq-openai-compatible",
                external_message_id=response.external_message_id,
                provider_id=provider.provider_id,
                model_id=provider.model_id,
                response_text=response.response_text,
            )
            print("LIVE_RESPONSE_INGESTION> PASS")
            print("REVIEW_EVENT_ID> " + ingested.event_id)
            print("ORION_RESPONSE_SHA256> " + ingested.response_sha256)

            event = store.get_event(ingested.event_id)
            if event is None:
                raise RuntimeError("ingested response event missing")
            if event.event_type != EventType.REVIEW:
                raise RuntimeError("live cloud response is not REVIEW")
            if event.parent_event_id != request.event_id:
                raise RuntimeError("live response not causally bound to request")
            body = event.payload.get("body") or {}
            if body.get("request_id") != request.request_id:
                raise RuntimeError("request id binding mismatch")
            if body.get("request_sha256") != request.request_sha256:
                raise RuntimeError("request hash binding mismatch")
            if body.get("provider_id") != provider.provider_id:
                raise RuntimeError("provider identity changed during ingestion")
            if body.get("model_id") != provider.model_id:
                raise RuntimeError("model identity changed during ingestion")
            if body.get("authority") != "advisory_only":
                raise RuntimeError("cloud response gained authority")
            if body.get("response_text") != response.response_text:
                raise RuntimeError("provider response changed during ingestion")
            print("LIVE_REQUEST_RESPONSE_BINDING> PASS")
            print("LIVE_RESPONSE_AUTHORITY_ADVISORY_ONLY> PASS")

            duplicate = control.ingest_cloud_specialist_response(
                request.request_id,
                source_system="groq-openai-compatible",
                external_message_id=response.external_message_id,
                provider_id=provider.provider_id,
                model_id=provider.model_id,
                response_text=response.response_text,
            )
            if not duplicate.duplicate or duplicate.event_id != ingested.event_id:
                raise RuntimeError("reingesting exact live response was not idempotent")
            print("LIVE_RESPONSE_REINGEST_IDEMPOTENT> PASS")

            inbox = exchange.inbox(
                task.project_id,
                task.task_id,
                "orion:governor",
            )
            if len(inbox) != 1 or inbox[0].event_id != ingested.event_id:
                raise RuntimeError("governor inbox missing exact live REVIEW")
            print("GOVERNOR_INBOX_LIVE_REVIEW> PASS")

            events = store.list_task_events(task.project_id, task.task_id)
            event_types = [item.event_type for item in events]
            if event_types != [EventType.PROPOSAL, EventType.REVIEW]:
                raise RuntimeError("unexpected live event chain: " + repr(event_types))
            if any(
                item.event_type in {EventType.DECISION, EventType.ACTION}
                for item in events
            ):
                raise RuntimeError("live cloud roundtrip minted execution authority")
            print("LIVE_CLOUD_DECISIONS_CREATED> 0")
            print("LIVE_CLOUD_ACTIONS_CREATED> 0")
            print("LIVE_CLOUD_HAND_EXECUTIONS> 0")
            print("LIVE_CLOUD_TOOLS_ENABLED> 0")
            print("LIVE_CLOUD_FALLBACK_SUBSTITUTIONS> 0")

            summary = {
                "schema": "orion.v3.live-cloud-roundtrip.v0",
                "run_id": "V3-RUN-047",
                "provider": provider.provider_id,
                "requested_model": provider.model_id,
                "served_model": response.served_model,
                "provider_external_message_id_present": True,
                "prompt_sha256": response.prompt_sha256,
                "provider_response_sha256": response.response_sha256,
                "orion_response_sha256": ingested.response_sha256,
                "response_chars": len(response.response_text),
                "latency_seconds": response.elapsed_seconds,
                "request_id": request.request_id,
                "request_sha256": request.request_sha256,
                "review_event_id": ingested.event_id,
                "event_type": "REVIEW",
                "authority": "advisory_only",
                "decisions_created": 0,
                "actions_created": 0,
                "hand_executions": 0,
                "tools_enabled": 0,
                "fallback_substitutions": 0,
            }
            print(
                "ORION_LIVE_CLOUD_ROUNDTRIP_SUMMARY> "
                + json.dumps(summary, ensure_ascii=False, sort_keys=True)
            )
        finally:
            store.close()

    print("ORION_LIVE_CLOUD_ROUNDTRIP> PASS")
    print("STATUS> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
