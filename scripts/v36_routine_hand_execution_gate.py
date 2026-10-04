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
    dispatch_governor_tool,
    execute_read_only_proposal,
    governor_control_tool_specs,
)
from orion_v3.state import EventType, OrionStateStore


MODEL = "qwen35-9b-orion:latest"
NUM_CTX = 4096
OLLAMA = "http://127.0.0.1:11434"
ACTOR = "qwen35-9b-orion"

SYSTEM_PROMPT = """You are ORION's production local governor.
Use only the ORION control tools provided.
You propose semantic capabilities; you never execute Hands directly.
Do not invent execution, approval, evidence, or success.
For the owner's request choose exactly one matching registered ORION capability.
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


def call_governor(prompt: str, tools: list[dict[str, Any]]) -> tuple[str, dict[str, Any], dict[str, Any]]:
    payload = {
        "model": MODEL,
        "stream": False,
        "think": True,
        "options": {
            "num_ctx": NUM_CTX,
            "temperature": 0,
        },
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "tools": tools,
    }
    started = time.perf_counter()
    response = request_json("/api/chat", payload, timeout=240.0)
    elapsed = round(time.perf_counter() - started, 3)
    message = response.get("message") or {}
    calls = message.get("tool_calls") or []
    if len(calls) != 1:
        raise RuntimeError(
            "expected exactly one governor tool call, got "
            + str(len(calls))
            + "; content="
            + repr(str(message.get("content") or "")[:1000])
        )
    function = calls[0].get("function") or {}
    name = str(function.get("name") or "")
    arguments = function.get("arguments") or {}
    if isinstance(arguments, str):
        arguments = json.loads(arguments)
    if not isinstance(arguments, dict):
        raise RuntimeError("governor arguments were not an object")
    trace = {
        "tool": name,
        "arguments": arguments,
        "elapsed_seconds": elapsed,
        "thinking_chars": len(str(message.get("thinking") or "")),
        "content_chars": len(str(message.get("content") or "")),
    }
    print("GOVERNOR_ROUTINE_TOOL_CALL> " + json.dumps(trace, ensure_ascii=False, sort_keys=True))
    return name, arguments, trace


def main() -> int:
    print("V3_RUN_ID> V3-RUN-049R")
    print("ORION_ROUTINE_HAND_EXECUTION> START")
    print("MODEL> " + MODEL)
    print("THINKING> ON")
    print("NUM_CTX> " + str(NUM_CTX))
    print("HAND> OpenJarvis orion_filesystem_search")
    print("AUTHORITY> canonical proposal -> ORION Action Lease -> Hand -> evidence -> verifier")

    ensure_ollama_and_model()

    with tempfile.TemporaryDirectory(prefix="orion-run049-") as td:
        store = OrionStateStore(Path(td) / "orion.db")
        store.initialize()
        try:
            project = store.create_project("RUN-049", project_id="run049-project")
            task = store.create_task(
                project.project_id,
                (
                    "Find pyproject.toml and gateway.py inside the active project. "
                    "Do not edit, reveal, open or publish anything."
                ),
                task_id="run049-task",
            )
            control = OperatorControlPlane(store)
            control.initialize()

            tools = governor_control_tool_specs(control.registry, include_resume=False)
            tool_name, arguments, trace = call_governor(
                (
                    "OWNER REQUEST:\n"
                    + task.objective
                    + "\nUse the exact registered ORION capability for an exact-basename search."
                ),
                tools,
            )
            if tool_name != "orion_capability_fs__search_exact":
                raise RuntimeError("governor chose wrong capability: " + tool_name)
            if set(arguments.get("exact_names") or []) != {
                "pyproject.toml",
                "gateway.py",
            }:
                raise RuntimeError("governor lost exact requested names")
            if arguments.get("locations") != ["active_project"]:
                raise RuntimeError("governor widened search location")
            print("GOVERNOR_CAPABILITY_SELECTION> PASS")

            proposal = dispatch_governor_tool(
                control,
                task_id=task.task_id,
                tool_name=tool_name,
                arguments=arguments,
                actor_id=ACTOR,
            )
            if proposal["kind"] != "capability_proposal":
                raise RuntimeError("governor did not create canonical capability proposal")
            if proposal["capability_id"] != "fs.search_exact":
                raise RuntimeError("canonical proposal capability mismatch")
            proposal_event_id = proposal["event_id"]
            print("CANONICAL_PROPOSAL> PASS " + proposal_event_id)
            print("CANONICAL_PROPOSAL_SHA256> " + proposal["action_sha256"])

            execution = execute_read_only_proposal(
                store,
                task_id=task.task_id,
                proposal_event_id=proposal_event_id,
                trusted_roots={"active_project": ROOT},
            )
            print("ORION_ACTION_LEASED_DISPATCH> PASS")
            print("ACTION_EVENT_ID> " + execution.action_event_id)
            print("EVIDENCE_EVENT_ID> " + execution.evidence_event_id)
            print("RESULT_EVENT_ID> " + execution.result_event_id)
            print("HAND_OUTCOME> " + execution.evidence.outcome.value)

            verified = dict(execution.verified_result)
            if verified.get("status") != "PASS":
                raise RuntimeError("deterministic verifier did not PASS")
            found_names = {str(name) for name in verified.get("found_names", [])}
            if not {"pyproject.toml", "gateway.py"}.issubset(found_names):
                raise RuntimeError(
                    "real Hand evidence did not contain both requested names: "
                    + repr(sorted(found_names))
                )
            matches = verified.get("matches")
            if not isinstance(matches, list):
                raise RuntimeError("verified matches missing")
            relative_paths = {
                str(item.get("relative_path") or "")
                for item in matches
                if isinstance(item, dict)
            }
            if "pyproject.toml" not in relative_paths:
                raise RuntimeError("root pyproject.toml not found by real Hand")
            if "src/orion_v3/authority/gateway.py" not in relative_paths:
                raise RuntimeError("authority gateway.py not found by real Hand")

            encoded = json.dumps(verified, ensure_ascii=False, sort_keys=True)
            if str(ROOT) in encoded:
                raise RuntimeError("trusted absolute root leaked into verified evidence")
            print("REAL_FILE_SEARCH_EVIDENCE> PASS")
            print("EXPECTED_RELATIVE_PATHS> PASS")
            print("TRUSTED_ROOT_LEAK> 0")
            print("DETERMINISTIC_VERIFICATION> PASS")

            events = store.list_task_events(task.project_id, task.task_id)
            types = [event.event_type for event in events]
            if types != [
                EventType.PROPOSAL,
                EventType.ACTION,
                EventType.EVIDENCE,
                EventType.RESULT,
            ]:
                raise RuntimeError("unexpected causal event chain: " + repr(types))
            if events[1].parent_event_id != events[0].event_id:
                raise RuntimeError("ACTION not parented to PROPOSAL")
            if events[2].parent_event_id != events[1].event_id:
                raise RuntimeError("EVIDENCE not parented to ACTION")
            if events[3].parent_event_id != events[2].event_id:
                raise RuntimeError("RESULT not parented to EVIDENCE")
            print("PROPOSAL_ACTION_EVIDENCE_RESULT_CHAIN> PASS")

            replay_blocked = False
            try:
                execute_read_only_proposal(
                    store,
                    task_id=task.task_id,
                    proposal_event_id=proposal_event_id,
                    trusted_roots={"active_project": ROOT},
                )
            except Exception as exc:
                if getattr(exc, "code", None) == "proposal_already_dispatched":
                    replay_blocked = True
                else:
                    raise
            if not replay_blocked:
                raise RuntimeError("same canonical proposal executed twice")
            print("DUPLICATE_PROPOSAL_DISPATCH> BLOCKED")

            summary = {
                "schema": "orion.v3.routine-hand-execution.v0",
                "run_id": "V3-RUN-049R",
                "model": MODEL,
                "thinking": "ON",
                "num_ctx": NUM_CTX,
                "capability_id": proposal["capability_id"],
                "proposal_event_id": proposal_event_id,
                "action_sha256": proposal["action_sha256"],
                "action_event_id": execution.action_event_id,
                "evidence_event_id": execution.evidence_event_id,
                "result_event_id": execution.result_event_id,
                "hand_implementation": execution.evidence.implementation_id,
                "hand_outcome": execution.evidence.outcome.value,
                "verified_found_names": sorted(found_names),
                "verified_match_count": verified.get("match_count"),
                "governor_trace": trace,
                "trusted_root_leak": False,
                "duplicate_dispatch_blocked": True,
                "external_provider_calls": 0,
            }
            print(
                "ORION_ROUTINE_HAND_SUMMARY> "
                + json.dumps(summary, ensure_ascii=False, sort_keys=True)
            )
        finally:
            store.close()

    print("ORION_ROUTINE_HAND_EXECUTION> PASS")
    print("STATUS> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
