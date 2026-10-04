from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OPENJARVIS_SRC = ROOT / "external" / "OpenJarvis" / "src"
if not OPENJARVIS_SRC.exists():
    raise SystemExit("Pinned OpenJarvis donor missing; run fetch_openjarvis.ps1 first.")
sys.path.insert(0, str(OPENJARVIS_SRC))
sys.path.insert(0, str(ROOT / "src"))

from orion_v3.operator import (
    OperatorControlPlane,
    TaskProgressState,
    decide_exact_search_task_progress,
    dispatch_governor_tool,
    execute_read_only_proposal,
    governor_control_tool_specs,
)
from orion_v3.state import EventType, OrionStateStore


MODEL = "qwen35-9b-orion:latest"
NUM_CTX = 4096
OLLAMA = "http://127.0.0.1:11434"
ACTOR = "qwen35-9b-orion"
MISSING_NAME = "__ORION_RUN051_PROVABLY_MISSING_5D6A2C91__.nope"

SYSTEM_PROMPT = """You are ORION's production local governor.
Choose only the semantic capability needed for the owner request.
You do not control execution-policy knobs, trusted roots, task completion state, or evidence truth.
Use only the provided ORION control tools.
Do not invent execution, approval, completion, or success.
"""


def request_json(path: str, payload: dict[str, Any] | None = None, timeout: float = 180.0) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        OLLAMA + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="GET" if payload is None else "POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        decoded = json.loads(response.read().decode("utf-8"))
    if not isinstance(decoded, dict):
        raise RuntimeError("Ollama returned non-object JSON")
    return decoded


def find_ollama() -> str | None:
    candidates: list[str] = []
    for name in ("ollama.exe", "ollama"):
        found = shutil.which(name)
        if found:
            candidates.append(found)
    local = os.environ.get("LOCALAPPDATA")
    program_files = os.environ.get("ProgramFiles")
    if local:
        candidates.extend(
            [
                str(Path(local) / "Programs" / "Ollama" / "ollama.exe"),
                str(Path(local) / "Ollama" / "ollama.exe"),
            ]
        )
    if program_files:
        candidates.append(str(Path(program_files) / "Ollama" / "ollama.exe"))
    for candidate in candidates:
        if Path(candidate).is_file():
            return candidate
    return None


def ensure_ollama_and_model() -> None:
    try:
        tags = request_json("/api/tags", timeout=2.0)
        print("OLLAMA_SERVICE> ALREADY_READY")
    except Exception:
        executable = find_ollama()
        if not executable:
            raise RuntimeError("Ollama unavailable and executable not found")
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
        subprocess.Popen(
            [executable, "serve"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=flags,
        )
        deadline = time.time() + 15.0
        last_error: Exception | None = None
        while time.time() < deadline:
            try:
                tags = request_json("/api/tags", timeout=2.0)
                print("OLLAMA_SERVICE> AUTO_STARTED")
                break
            except Exception as exc:
                last_error = exc
                time.sleep(0.25)
        else:
            raise RuntimeError("Ollama did not become ready") from last_error

    names = {
        str(item.get("name") or item.get("model") or "")
        for item in tags.get("models", [])
        if isinstance(item, dict)
    }
    if MODEL not in names:
        raise RuntimeError("required governor model missing: " + MODEL)
    print("LOCAL_GOVERNOR_MODEL> AVAILABLE " + MODEL)


def call_governor(owner_request: str, tools: list[dict[str, Any]], label: str):
    payload = {
        "model": MODEL,
        "stream": False,
        "think": True,
        "options": {"num_ctx": NUM_CTX, "temperature": 0},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "OWNER REQUEST:\n" + owner_request},
        ],
        "tools": tools,
    }
    started = time.perf_counter()
    response = request_json("/api/chat", payload, timeout=240.0)
    elapsed = round(time.perf_counter() - started, 3)
    message = response.get("message") or {}
    calls = message.get("tool_calls") or []
    if len(calls) != 1:
        raise RuntimeError(label + " expected exactly one governor tool call")
    function = calls[0].get("function") or {}
    name = str(function.get("name") or "")
    arguments = function.get("arguments") or {}
    if isinstance(arguments, str):
        arguments = json.loads(arguments)
    if not isinstance(arguments, dict):
        raise RuntimeError(label + " arguments were not an object")
    trace = {
        "label": label,
        "tool": name,
        "arguments": arguments,
        "elapsed_seconds": elapsed,
        "thinking_chars": len(str(message.get("thinking") or "")),
    }
    print("GOVERNOR_TASK_SELECTION> " + json.dumps(trace, ensure_ascii=False, sort_keys=True))
    return name, arguments, trace


def run_search_task(
    store: OrionStateStore,
    control: OperatorControlPlane,
    *,
    project_id: str,
    task_id: str,
    owner_request: str,
    required_names: list[str],
    tools: list[dict[str, Any]],
    label: str,
):
    task = store.create_task(
        project_id,
        owner_request,
        task_id=task_id,
    )
    tool_name, arguments, trace = call_governor(owner_request, tools, label)

    if tool_name != "orion_capability_fs__search_exact":
        raise RuntimeError(label + " chose wrong capability: " + tool_name)
    if set(arguments) != {"exact_names", "locations"}:
        raise RuntimeError(label + " governor gained execution-policy knobs")
    if arguments.get("exact_names") != required_names:
        raise RuntimeError(
            label + " changed requested exact names: " + repr(arguments.get("exact_names"))
        )
    if arguments.get("locations") != ["active_project"]:
        raise RuntimeError(label + " changed requested location")

    proposal = dispatch_governor_tool(
        control,
        task_id=task.task_id,
        tool_name=tool_name,
        arguments=arguments,
        actor_id=ACTOR,
    )
    execution = execute_read_only_proposal(
        store,
        task_id=task.task_id,
        proposal_event_id=proposal["event_id"],
        trusted_roots={"active_project": ROOT},
    )
    decision = decide_exact_search_task_progress(
        store,
        task_id=task.task_id,
        result_event_id=execution.result_event_id,
        required_exact_names=required_names,
        required_locations=["active_project"],
    )
    return task, proposal, execution, decision, trace


def main() -> int:
    print("V3_RUN_ID> V3-RUN-051")
    print("ORION_TASK_PROGRESS_AUTHORITY> START")
    print("MODEL> " + MODEL)
    print("THINKING> ON")
    print("NUM_CTX> " + str(NUM_CTX))
    print("AUTHORITY> model chooses semantics; ORION owns task completion/progress")

    if any(path.name == MISSING_NAME for path in ROOT.rglob(MISSING_NAME)):
        raise RuntimeError("RUN-051 missing-name precondition unexpectedly exists")
    print("MISSING_NAME_PRECONDITION> PASS")

    ensure_ollama_and_model()

    with tempfile.TemporaryDirectory(prefix="orion-run051-") as td:
        db = Path(td) / "orion.db"
        store = OrionStateStore(db)
        store.initialize()
        project = store.create_project("RUN-051", project_id="run051-project")
        control = OperatorControlPlane(store)
        control.initialize()

        try:
            tools = governor_control_tool_specs(control.registry, include_resume=False)
            tool_names = {item["function"]["name"] for item in tools}
            if any("complete" in name or "status" in name for name in tool_names):
                raise RuntimeError("model-facing governor unexpectedly exposes task completion authority")
            print("MODEL_TASK_COMPLETION_TOOL> 0")

            complete_names = ["pyproject.toml", "gateway.py"]
            complete_request = (
                "Find pyproject.toml and gateway.py inside active_project. "
                "This task is complete only when ORION has verified both basenames."
            )
            task_a, proposal_a, execution_a, decision_a, trace_a = run_search_task(
                store,
                control,
                project_id=project.project_id,
                task_id="run051-complete",
                owner_request=complete_request,
                required_names=complete_names,
                tools=tools,
                label="COMPLETE_CASE",
            )

            if decision_a.state != TaskProgressState.COMPLETED:
                raise RuntimeError("complete case was not deterministically COMPLETED")
            if decision_a.missing_names:
                raise RuntimeError("complete case unexpectedly has missing names")
            task_a_after = store.get_task(task_a.task_id)
            if task_a_after is None or task_a_after.status != "completed":
                raise RuntimeError("complete task status did not become completed")
            print("COMPLETE_CASE_ORION_DECISION> PASS COMPLETED")
            print("COMPLETE_CASE_MODEL_STATUS_AUTHORITY> 0")

            duplicate_a = decide_exact_search_task_progress(
                store,
                task_id=task_a.task_id,
                result_event_id=execution_a.result_event_id,
                required_exact_names=complete_names,
                required_locations=["active_project"],
            )
            if not duplicate_a.duplicate:
                raise RuntimeError("complete decision retry created duplicate canonical state")
            if duplicate_a.decision_event_id != decision_a.decision_event_id:
                raise RuntimeError("complete decision retry changed decision identity")
            print("COMPLETE_DECISION_RETRY> IDEMPOTENT")

            partial_names = ["pyproject.toml", MISSING_NAME]
            partial_request = (
                "Find pyproject.toml and "
                + MISSING_NAME
                + " inside active_project. This task is complete only when ORION has "
                "verified both exact basenames."
            )
            task_b, proposal_b, execution_b, decision_b, trace_b = run_search_task(
                store,
                control,
                project_id=project.project_id,
                task_id="run051-incomplete",
                owner_request=partial_request,
                required_names=partial_names,
                tools=tools,
                label="INCOMPLETE_CASE",
            )

            if decision_b.state != TaskProgressState.NEEDS_NEXT_STEP:
                raise RuntimeError("incomplete case was not NEEDS_NEXT_STEP")
            if decision_b.missing_names != (MISSING_NAME,):
                raise RuntimeError(
                    "incomplete case missing-name evidence mismatch: "
                    + repr(decision_b.missing_names)
                )
            task_b_after = store.get_task(task_b.task_id)
            if task_b_after is None or task_b_after.status != "needs_next_step":
                raise RuntimeError("incomplete task status did not become needs_next_step")
            print("INCOMPLETE_CASE_ORION_DECISION> PASS NEEDS_NEXT_STEP")
            print("INCOMPLETE_REQUIRED_NAME> " + MISSING_NAME)
            print("INCOMPLETE_CASE_MODEL_STATUS_AUTHORITY> 0")

            duplicate_b = decide_exact_search_task_progress(
                store,
                task_id=task_b.task_id,
                result_event_id=execution_b.result_event_id,
                required_exact_names=partial_names,
                required_locations=["active_project"],
            )
            if not duplicate_b.duplicate:
                raise RuntimeError("incomplete decision retry created duplicate canonical state")
            print("INCOMPLETE_DECISION_RETRY> IDEMPOTENT")

            for task_id, expected_state in (
                (task_a.task_id, "COMPLETED"),
                (task_b.task_id, "NEEDS_NEXT_STEP"),
            ):
                events = store.list_task_events(project.project_id, task_id)
                types = [event.event_type for event in events]
                if types != [
                    EventType.PROPOSAL,
                    EventType.ACTION,
                    EventType.EVIDENCE,
                    EventType.RESULT,
                    EventType.DECISION,
                ]:
                    raise RuntimeError(task_id + " unexpected event chain: " + repr(types))
                decision_event = events[-1]
                if decision_event.parent_event_id != events[-2].event_id:
                    raise RuntimeError(task_id + " DECISION is not parented to RESULT")
                if decision_event.payload.get("state") != expected_state:
                    raise RuntimeError(task_id + " DECISION state mismatch")
                if decision_event.payload.get("authority") != "orion_deterministic_policy":
                    raise RuntimeError(task_id + " task state authority marker mismatch")
            print("TASK_PROGRESS_CAUSAL_CHAINS> PASS")

            store.close()

            reopened = OrionStateStore(db)
            reopened.initialize()
            try:
                persisted_a = reopened.get_task(task_a.task_id)
                persisted_b = reopened.get_task(task_b.task_id)
                if persisted_a is None or persisted_a.status != "completed":
                    raise RuntimeError("completed task status did not survive restart")
                if persisted_b is None or persisted_b.status != "needs_next_step":
                    raise RuntimeError("needs_next_step task status did not survive restart")
                events_a = reopened.list_task_events(project.project_id, task_a.task_id)
                events_b = reopened.list_task_events(project.project_id, task_b.task_id)
                if events_a[-1].event_type != EventType.DECISION:
                    raise RuntimeError("complete DECISION did not survive restart")
                if events_b[-1].event_type != EventType.DECISION:
                    raise RuntimeError("incomplete DECISION did not survive restart")
            finally:
                reopened.close()
            print("TASK_PROGRESS_RESTART_PERSISTENCE> PASS")

            summary = {
                "schema": "orion.v3.task-progress-authority.v0",
                "run_id": "V3-RUN-051",
                "model": MODEL,
                "thinking": "ON",
                "num_ctx": NUM_CTX,
                "model_task_completion_tools": 0,
                "complete_case": {
                    "proposal_event_id": proposal_a["event_id"],
                    "result_event_id": execution_a.result_event_id,
                    "decision_event_id": decision_a.decision_event_id,
                    "state": decision_a.state.value,
                    "missing_names": list(decision_a.missing_names),
                    "duplicate_retry_idempotent": True,
                    "governor_trace": trace_a,
                },
                "incomplete_case": {
                    "proposal_event_id": proposal_b["event_id"],
                    "result_event_id": execution_b.result_event_id,
                    "decision_event_id": decision_b.decision_event_id,
                    "state": decision_b.state.value,
                    "missing_names": list(decision_b.missing_names),
                    "duplicate_retry_idempotent": True,
                    "governor_trace": trace_b,
                },
                "decision_authority": "orion_deterministic_policy",
                "restart_persistence": True,
                "external_provider_calls": 0,
            }
            print(
                "ORION_TASK_PROGRESS_SUMMARY> "
                + json.dumps(summary, ensure_ascii=False, sort_keys=True)
            )
        finally:
            store.close()

    print("ORION_TASK_PROGRESS_AUTHORITY> PASS")
    print("STATUS> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
