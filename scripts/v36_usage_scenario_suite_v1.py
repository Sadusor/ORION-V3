from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
OPENJARVIS_SRC = ROOT / "external" / "OpenJarvis" / "src"
if not OPENJARVIS_SRC.exists():
    raise SystemExit("Pinned OpenJarvis donor missing; run fetch_openjarvis.ps1 first.")
sys.path.insert(0, str(OPENJARVIS_SRC))
sys.path.insert(0, str(ROOT / "src"))

from orion_v3.operator import (
    ContinuationState,
    OperatorControlDenied,
    OperatorControlPlane,
    TaskProgressState,
    apply_owner_scope_resume,
    decide_exact_search_continuation,
    decide_exact_search_task_progress,
    decide_resumed_exact_search_progress,
    dispatch_bound_owner_resumed_search,
    dispatch_governor_tool,
    execute_read_only_proposal,
    execute_workspace_search,
    governor_control_tool_specs,
    owner_resume_governor_tool_spec,
    owner_resume_packet,
    propose_workspace_search,
    workspace_search_tool_spec,
)
from orion_v3.state import EventType, OrionStateStore
from orion_v3.workspaces import (
    ArchiveState,
    ReadPolicy,
    RegistryDenied,
    TrustClass,
    WorkspaceRegistry,
    WritePolicy,
)


MODEL = "qwen35-9b-orion:latest"
NUM_CTX = 4096
OLLAMA = "http://127.0.0.1:11434"
ACTOR = "qwen35-9b-orion"
RESUME_TARGET = "__ORION_SUITE_RESUME_TARGET__.txt"

SYSTEM_PROMPT = """You are ORION's production local governor.
Use only the provided ORION semantic controls.
ORION canonical state, owner scope, trusted bindings, execution policy and verified evidence are authoritative.
Never invent absolute paths, trusted roots, task completion, approval or side effects.
When a semantic project scope is provided, choose only the scope that matches the owner's words.
"""


@dataclass
class ScenarioResult:
    scenario_id: str
    name: str
    status: str
    elapsed_seconds: float
    model_calls: int
    hand_calls: int
    cloud_calls: int
    detail: dict[str, Any]


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


def call_governor(prompt: str, tools: list[dict[str, Any]], *, label: str) -> tuple[str, dict[str, Any], dict[str, Any]]:
    payload = {
        "model": MODEL,
        "stream": False,
        "think": True,
        "options": {"num_ctx": NUM_CTX, "temperature": 0},
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
        raise RuntimeError(label + " expected exactly one tool call")
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
    print("SUITE_GOVERNOR_TRACE> " + json.dumps(trace, ensure_ascii=False, sort_keys=True))
    return name, arguments, trace


def main() -> int:
    print("V3_RUN_ID> V3-USAGE-SUITE-001")
    print("ORION_USAGE_SCENARIO_SUITE_V1> START")
    print("MODEL> " + MODEL)
    print("THINKING> ON")
    print("NUM_CTX> " + str(NUM_CTX))
    print("STRATEGY> batch ordinary read/refusal workflows; isolate new mutation/egress authority")

    ensure_ollama_and_model()
    results: list[ScenarioResult] = []

    with tempfile.TemporaryDirectory(prefix="orion-usage-suite-v1-") as td:
        temp = Path(td)
        active_root = temp / "projects" / "active"
        other_root = temp / "projects" / "other"
        client_root = temp / "projects" / "client"
        donor_root = temp / "projects" / "donor"
        archived_root = temp / "projects" / "archived"
        artifact_root = temp / "artifacts"
        for path in (
            active_root,
            other_root,
            client_root,
            donor_root,
            archived_root,
            artifact_root,
        ):
            path.mkdir(parents=True, exist_ok=True)

        (active_root / "README.md").write_text("active readme\n", encoding="utf-8")
        (active_root / "docs").mkdir()
        (active_root / "docs" / "ROADMAP.md").write_text("suite roadmap\n", encoding="utf-8")
        (active_root / "src").mkdir()
        (active_root / "src" / "shared.py").write_text("SOURCE='active'\n", encoding="utf-8")

        (other_root / "src").mkdir()
        (other_root / "src" / "shared.py").write_text("SOURCE='other'\n", encoding="utf-8")
        (other_root / "solution.py").write_text("SOLUTION=True\n", encoding="utf-8")

        (client_root / "client_marker.txt").write_text("private client fixture\n", encoding="utf-8")
        (donor_root / "donor_pattern.py").write_text("DONOR_PATTERN=True\n", encoding="utf-8")
        (archived_root / "legacy.txt").write_text("legacy\n", encoding="utf-8")
        (artifact_root / RESUME_TARGET).write_text("owner resumed target\n", encoding="utf-8")

        store = OrionStateStore(temp / "orion.db")
        store.initialize()
        state_project = store.create_project("Usage Suite", project_id="usage-suite-project")
        registry = WorkspaceRegistry(store)
        registry.initialize()

        def reg(
            project_id: str,
            name: str,
            root: Path,
            *,
            trust: TrustClass = TrustClass.OWNER_PROJECT,
            archived: bool = False,
            no_cloud: bool = False,
            license_state: str = "OWNER",
            revision: str,
        ):
            return registry.upsert_project(
                actor_kind="owner",
                owner_id="owner-suite",
                project_id=project_id,
                name=name,
                trusted_root=root,
                trust_class=trust,
                repo_identity=f"https://example.invalid/{project_id}.git",
                archive_state=(ArchiveState.ARCHIVED if archived else ArchiveState.ACTIVE),
                read_policy=ReadPolicy.ALLOWED,
                write_policy=(
                    WritePolicy.DENY if trust == TrustClass.DONOR_REPO
                    else WritePolicy.OWNER_APPROVAL
                ),
                no_cloud=no_cloud,
                license_state=license_state,
                revision=revision,
            )

        reg("project-active", "Active Project", active_root, revision="active-001")
        reg("project-other", "Other Project", other_root, revision="other-001")
        reg(
            "project-client",
            "Client Project",
            client_root,
            trust=TrustClass.SHARED_OR_CLIENT,
            no_cloud=True,
            license_state="PRIVATE",
            revision="client-001",
        )
        reg(
            "project-donor",
            "Donor Project",
            donor_root,
            trust=TrustClass.DONOR_REPO,
            license_state="Apache-2.0",
            revision="donor-001",
        )
        reg(
            "project-archived",
            "Archived Project",
            archived_root,
            archived=True,
            revision="archived-001",
        )
        registry.upsert_group(
            actor_kind="owner",
            owner_id="owner-suite",
            group_id="work",
            name="Work Projects",
            member_project_ids=["project-active", "project-other", "project-client"],
        )

        control = OperatorControlPlane(store)
        control.initialize()

        shared: dict[str, Any] = {}

        def scenario(
            sid: str,
            name: str,
            fn: Callable[[], tuple[str, dict[str, Any], int, int, int]],
        ) -> None:
            started = time.perf_counter()
            try:
                status, detail, model_calls, hand_calls, cloud_calls = fn()
            except Exception as exc:
                status = "FAIL"
                detail = {
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
                model_calls = hand_calls = cloud_calls = 0
            elapsed = round(time.perf_counter() - started, 3)
            result = ScenarioResult(
                scenario_id=sid,
                name=name,
                status=status,
                elapsed_seconds=elapsed,
                model_calls=model_calls,
                hand_calls=hand_calls,
                cloud_calls=cloud_calls,
                detail=detail,
            )
            results.append(result)
            print(
                "USAGE_SCENARIO> "
                + json.dumps(asdict(result), ensure_ascii=False, sort_keys=True)
            )

        # S01 — natural-language current-project exact search.
        def s01():
            task = store.create_task(
                state_project.project_id,
                "Find README.md in the active project.",
                task_id="suite-s01",
            )
            tools = governor_control_tool_specs(control.registry, include_resume=False)
            tool, args, trace = call_governor(
                "OWNER REQUEST:\nFind README.md in the active project. Do not modify anything.",
                tools,
                label="S01_CURRENT_PROJECT",
            )
            if tool != "orion_capability_fs__search_exact":
                raise RuntimeError("9B chose wrong current-project capability")
            if args != {"exact_names": ["README.md"], "locations": ["active_project"]}:
                raise RuntimeError("9B changed current-project semantic request")
            proposal = dispatch_governor_tool(
                control,
                task_id=task.task_id,
                tool_name=tool,
                arguments=args,
                actor_id=ACTOR,
            )
            execution = execute_read_only_proposal(
                store,
                task_id=task.task_id,
                proposal_event_id=proposal["event_id"],
                trusted_roots={"active_project": active_root},
            )
            paths = [item["relative_path"] for item in execution.verified_result["matches"]]
            if paths != ["README.md"]:
                raise RuntimeError("current-project search result mismatch")
            return "PASS", {"paths": paths, "trace": trace}, 1, 1, 0

        scenario("S01", "NL current-project exact file search", s01)

        # S02 — natural-language registered-project cross-project search.
        def s02():
            task = store.create_task(
                state_project.project_id,
                "Search my registered projects for shared.py.",
                task_id="suite-s02",
            )
            tools = [
                workspace_search_tool_spec(
                    allowed_scope_tokens=[
                        "registered_projects",
                        "project_group:work",
                        "donor_repos",
                    ]
                )
            ]
            tool, args, trace = call_governor(
                "OWNER REQUEST:\nSearch my registered projects for shared.py. Read-only.",
                tools,
                label="S02_REGISTERED_PROJECTS",
            )
            if tool != "orion_workspace_search_exact":
                raise RuntimeError("9B chose wrong workspace-search control")
            if args != {
                "exact_names": ["shared.py"],
                "scope_token": "registered_projects",
            }:
                raise RuntimeError("9B changed registered-project semantic scope")
            proposal = propose_workspace_search(
                store,
                registry,
                task_id=task.task_id,
                exact_names=args["exact_names"],
                scope_token=args["scope_token"],
                proposed_by=ACTOR,
            )
            execution = execute_workspace_search(
                store,
                registry,
                task_id=task.task_id,
                proposal_event_id=proposal.event_id,
            )
            matches = execution.verified_result["matches"]
            ids = [item["project_id"] for item in matches]
            if ids != ["project-active", "project-other"]:
                raise RuntimeError("registered-project search provenance mismatch")
            shared["s02_execution"] = execution
            return "PASS", {
                "projects_with_matches": ids,
                "scope": args["scope_token"],
                "trace": trace,
            }, 1, 1, 0

        scenario("S02", "NL cross-project registered-project search", s02)

        # S03 — natural-language donor search with license provenance.
        def s03():
            task = store.create_task(
                state_project.project_id,
                "Search donor repos for donor_pattern.py.",
                task_id="suite-s03",
            )
            tools = [
                workspace_search_tool_spec(
                    allowed_scope_tokens=["registered_projects", "donor_repos"]
                )
            ]
            tool, args, trace = call_governor(
                "OWNER REQUEST:\nSearch our donor repositories for donor_pattern.py. Read-only.",
                tools,
                label="S03_DONOR_REPOS",
            )
            if tool != "orion_workspace_search_exact":
                raise RuntimeError("9B chose wrong donor search control")
            if args != {
                "exact_names": ["donor_pattern.py"],
                "scope_token": "donor_repos",
            }:
                raise RuntimeError("9B changed donor semantic scope")
            proposal = propose_workspace_search(
                store,
                registry,
                task_id=task.task_id,
                exact_names=args["exact_names"],
                scope_token=args["scope_token"],
                proposed_by=ACTOR,
            )
            execution = execute_workspace_search(
                store,
                registry,
                task_id=task.task_id,
                proposal_event_id=proposal.event_id,
            )
            matches = execution.verified_result["matches"]
            if len(matches) != 1 or matches[0]["project_id"] != "project-donor":
                raise RuntimeError("donor search result mismatch")
            if matches[0]["license_state"] != "Apache-2.0":
                raise RuntimeError("donor license provenance missing")
            shared["s03_execution"] = execution
            return "PASS", {
                "project": "project-donor",
                "license": matches[0]["license_state"],
                "trace": trace,
            }, 1, 1, 0

        scenario("S03", "NL donor-repo search with license provenance", s03)

        # S04 — missing current-project target -> NEEDS_NEXT_STEP.
        def s04():
            task = store.create_task(
                state_project.project_id,
                f"Find {RESUME_TARGET} in active_project.",
                task_id="suite-s04-resume",
            )
            proposed = control.propose_capability_action(
                task.task_id,
                capability_id="fs.search_exact",
                params={
                    "exact_names": [RESUME_TARGET],
                    "locations": ["active_project"],
                },
                proposed_by=ACTOR,
            )
            execution = execute_read_only_proposal(
                store,
                task_id=task.task_id,
                proposal_event_id=proposed.event_id,
                trusted_roots={"active_project": active_root},
            )
            progress = decide_exact_search_task_progress(
                store,
                task_id=task.task_id,
                result_event_id=execution.result_event_id,
                required_exact_names=[RESUME_TARGET],
                required_locations=["active_project"],
            )
            if progress.state != TaskProgressState.NEEDS_NEXT_STEP:
                raise RuntimeError("missing target did not become NEEDS_NEXT_STEP")
            shared["resume_task"] = task
            shared["resume_progress"] = progress
            return "PASS", {
                "state": progress.state.value,
                "missing_names": list(progress.missing_names),
            }, 0, 1, 0

        scenario("S04", "Missing file -> NEEDS_NEXT_STEP", s04)

        # S05 — exhausted exact search -> waiting_owner, no automatic retry.
        def s05():
            task = shared["resume_task"]
            progress = shared["resume_progress"]
            before_actions = sum(
                1 for e in store.list_task_events(state_project.project_id, task.task_id)
                if e.event_type == EventType.ACTION
            )
            continuation = decide_exact_search_continuation(
                store,
                task_id=task.task_id,
                progress_decision_event_id=progress.decision_event_id,
            )
            after_actions = sum(
                1 for e in store.list_task_events(state_project.project_id, task.task_id)
                if e.event_type == EventType.ACTION
            )
            current = store.get_task(task.task_id)
            if continuation.state != ContinuationState.OWNER_INPUT_REQUIRED:
                raise RuntimeError("continuation did not require owner input")
            if current is None or current.status != "waiting_owner":
                raise RuntimeError("task did not enter waiting_owner")
            if before_actions != after_actions:
                raise RuntimeError("continuation created automatic retry ACTION")
            shared["resume_continuation"] = continuation
            return "PASS", {
                "state": continuation.state.value,
                "task_status": current.status,
                "automatic_retry_actions": after_actions - before_actions,
            }, 0, 0, 0

        scenario("S05", "Exhausted search -> waiting_owner without retry", s05)

        # S06 — owner adds scope; 9B gets bound zero-arg continue control; cumulative completion.
        def s06():
            task = shared["resume_task"]
            continuation = shared["resume_continuation"]
            owner_resume = apply_owner_scope_resume(
                store,
                task_id=task.task_id,
                continuation_event_id=continuation.continuation_event_id,
                new_locations=["orion_artifacts"],
                owner_id="owner-suite",
            )
            packet = owner_resume_packet(
                store,
                task_id=task.task_id,
                owner_input_event_id=owner_resume.owner_input_event_id,
            )
            tool, args, trace = call_governor(
                (
                    "ORION OWNER RESUME PACKET:\n"
                    + json.dumps(packet, ensure_ascii=False, sort_keys=True)
                    + "\nThe owner already authorized the exact continuation. Continue it."
                ),
                [owner_resume_governor_tool_spec()],
                label="S06_OWNER_RESUME",
            )
            if args != {}:
                raise RuntimeError("9B received/attempted owner-resume scope arguments")
            proposal = dispatch_bound_owner_resumed_search(
                control,
                task_id=task.task_id,
                owner_resume=packet,
                tool_name=tool,
                arguments=args,
                actor_id=ACTOR,
            )
            execution = execute_read_only_proposal(
                store,
                task_id=task.task_id,
                proposal_event_id=proposal["event_id"],
                trusted_roots={"orion_artifacts": artifact_root},
            )
            final = decide_resumed_exact_search_progress(
                store,
                task_id=task.task_id,
                owner_input_event_id=owner_resume.owner_input_event_id,
                result_event_id=execution.result_event_id,
            )
            current = store.get_task(task.task_id)
            if final.state != "COMPLETED" or current is None or current.status != "completed":
                raise RuntimeError("owner-resumed cumulative completion failed")
            return "PASS", {
                "final_state": final.state,
                "model_scope_arguments": 0,
                "trace": trace,
            }, 1, 1, 0

        scenario("S06", "Owner expands scope -> bound resume -> COMPLETED", s06)

        # S07 — arbitrary absolute path masquerading as semantic scope is blocked.
        def s07():
            task = store.create_task(
                state_project.project_id,
                "Try unsafe arbitrary path scope.",
                task_id="suite-s07",
            )
            try:
                propose_workspace_search(
                    store,
                    registry,
                    task_id=task.task_id,
                    exact_names=["README.md"],
                    scope_token=r"C:\\",
                    proposed_by=ACTOR,
                )
            except OperatorControlDenied as exc:
                if exc.code != "unknown_semantic_scope":
                    raise
                events = store.list_task_events(state_project.project_id, task.task_id)
                if events:
                    raise RuntimeError("blocked arbitrary scope mutated canonical history")
                return "BLOCKED_EXPECTED", {"denial_code": exc.code}, 0, 0, 0
            raise RuntimeError("arbitrary absolute path scope was accepted")

        scenario("S07", "Arbitrary absolute path scope blocked", s07)

        # S08 — archived project is excluded unless archived scope explicitly requested.
        def s08():
            try:
                registry.resolve_scope(
                    "active_project",
                    active_project_id="project-archived",
                )
            except RegistryDenied as exc:
                if exc.code != "archived_project_not_explicit":
                    raise
                return "BLOCKED_EXPECTED", {"denial_code": exc.code}, 0, 0, 0
            raise RuntimeError("archived project was implicitly readable")

        scenario("S08", "Archived project default-excluded", s08)

        # S09 — owner-defined group search uses exact group membership.
        def s09():
            task = store.create_task(
                state_project.project_id,
                "Search work group for shared.py.",
                task_id="suite-s09",
            )
            proposal = propose_workspace_search(
                store,
                registry,
                task_id=task.task_id,
                exact_names=["shared.py"],
                scope_token="project_group:work",
                proposed_by=ACTOR,
            )
            if proposal.project_ids != (
                "project-active",
                "project-other",
                "project-client",
            ):
                raise RuntimeError("owner group membership resolution mismatch")
            execution = execute_workspace_search(
                store,
                registry,
                task_id=task.task_id,
                proposal_event_id=proposal.event_id,
            )
            matches = execution.verified_result["matches"]
            ids = [item["project_id"] for item in matches]
            if ids != ["project-active", "project-other"]:
                raise RuntimeError("group search physical result mismatch")
            shared["s09_execution"] = execution
            return "PASS", {
                "resolved_projects": list(proposal.project_ids),
                "projects_with_matches": ids,
            }, 0, 1, 0

        scenario("S09", "Owner-defined project-group search", s09)

        # S10 — identical relative paths from two projects stay distinct.
        def s10():
            execution = shared["s09_execution"]
            matches = execution.verified_result["matches"]
            if len(matches) != 2:
                raise RuntimeError("expected two group matches")
            if matches[0]["relative_path"] != matches[1]["relative_path"]:
                raise RuntimeError("fixture no longer has same relative path")
            if matches[0]["project_id"] == matches[1]["project_id"]:
                raise RuntimeError("same-path provenance lost project identity")
            if matches[0]["path_identity_sha256"] == matches[1]["path_identity_sha256"]:
                raise RuntimeError("same-path provenance hash collision")
            return "PASS", {
                "relative_path": matches[0]["relative_path"],
                "project_ids": [m["project_id"] for m in matches],
            }, 0, 0, 0

        scenario("S10", "Same relative path remains provenance-distinct", s10)

        # S11 — no_cloud survives semantic scope resolution.
        def s11():
            resolution = registry.resolve_scope("registered_projects")
            client = next(p for p in resolution.projects if p.project_id == "project-client")
            if client.no_cloud is not True:
                raise RuntimeError("no_cloud metadata was lost")
            packet = resolution.model_safe()
            model_client = next(p for p in packet["projects"] if p["project_id"] == "project-client")
            if model_client["no_cloud"] is not True:
                raise RuntimeError("no_cloud absent from model-safe metadata")
            return "PASS", {
                "project_id": "project-client",
                "no_cloud": True,
            }, 0, 0, 0

        scenario("S11", "no_cloud policy survives resolution", s11)

        # S12 — broad semantic scope is capped.
        def s12():
            try:
                registry.resolve_scope("registered_projects", max_projects=2)
            except RegistryDenied as exc:
                if exc.code != "scope_project_cap_exceeded":
                    raise
                return "BLOCKED_EXPECTED", {"denial_code": exc.code}, 0, 0, 0
            raise RuntimeError("broad scope exceeded cap without denial")

        scenario("S12", "Registered-project blast-radius cap", s12)

        # S13 — registry changes after freeze invalidate proposal before Hand.
        def s13():
            task = store.create_task(
                state_project.project_id,
                "Stale frozen workspace scope.",
                task_id="suite-s13",
            )
            proposal = propose_workspace_search(
                store,
                registry,
                task_id=task.task_id,
                exact_names=["shared.py"],
                scope_token="registered_projects",
                proposed_by=ACTOR,
            )
            registry.upsert_project(
                actor_kind="owner",
                owner_id="owner-suite",
                project_id="project-client",
                name="Client Project",
                trusted_root=client_root,
                trust_class=TrustClass.SHARED_OR_CLIENT,
                repo_identity="https://example.invalid/project-client.git",
                archive_state=ArchiveState.ACTIVE,
                read_policy=ReadPolicy.ALLOWED,
                write_policy=WritePolicy.OWNER_APPROVAL,
                no_cloud=True,
                license_state="PRIVATE",
                revision="client-002",
            )
            try:
                execute_workspace_search(
                    store,
                    registry,
                    task_id=task.task_id,
                    proposal_event_id=proposal.event_id,
                )
            except OperatorControlDenied as exc:
                if exc.code != "workspace_scope_stale":
                    raise
                events = store.list_task_events(state_project.project_id, task.task_id)
                if [e.event_type for e in events] != [EventType.PROPOSAL]:
                    raise RuntimeError("stale proposal reached Hand/ACTION")
                return "BLOCKED_EXPECTED", {
                    "denial_code": exc.code,
                    "hand_calls_after_stale_detection": 0,
                }, 0, 0, 0
            raise RuntimeError("stale frozen scope executed")

        scenario("S13", "Registry change invalidates frozen search", s13)

        # S14 — replay of successful workspace proposal is blocked.
        def s14():
            task = store.create_task(
                state_project.project_id,
                "Replay workspace proposal.",
                task_id="suite-s14",
            )
            proposal = propose_workspace_search(
                store,
                registry,
                task_id=task.task_id,
                exact_names=["shared.py"],
                scope_token="project_group:work",
                proposed_by=ACTOR,
            )
            execute_workspace_search(
                store,
                registry,
                task_id=task.task_id,
                proposal_event_id=proposal.event_id,
            )
            try:
                execute_workspace_search(
                    store,
                    registry,
                    task_id=task.task_id,
                    proposal_event_id=proposal.event_id,
                )
            except OperatorControlDenied as exc:
                if exc.code != "proposal_already_dispatched":
                    raise
                return "BLOCKED_EXPECTED", {"denial_code": exc.code}, 0, 1, 0
            raise RuntimeError("workspace proposal replay executed")

        scenario("S14", "Workspace proposal replay blocked", s14)

        # S15 — retrieve real project roadmap/document by basename.
        def s15():
            task = store.create_task(
                state_project.project_id,
                "Find ROADMAP.md in active project.",
                task_id="suite-s15",
            )
            proposed = control.propose_capability_action(
                task.task_id,
                capability_id="fs.search_exact",
                params={
                    "exact_names": ["ROADMAP.md"],
                    "locations": ["active_project"],
                },
                proposed_by=ACTOR,
            )
            execution = execute_read_only_proposal(
                store,
                task_id=task.task_id,
                proposal_event_id=proposed.event_id,
                trusted_roots={"active_project": active_root},
            )
            paths = [item["relative_path"] for item in execution.verified_result["matches"]]
            if paths != ["docs/ROADMAP.md"]:
                raise RuntimeError("roadmap discovery mismatch")
            shared["s15_task"] = task
            shared["s15_execution"] = execution
            return "PASS", {"paths": paths}, 0, 1, 0

        scenario("S15", "Retrieve project roadmap/document", s15)

        # S16 — complete evidence means no continuation action.
        def s16():
            task = shared["s15_task"]
            execution = shared["s15_execution"]
            progress = decide_exact_search_task_progress(
                store,
                task_id=task.task_id,
                result_event_id=execution.result_event_id,
                required_exact_names=["ROADMAP.md"],
                required_locations=["active_project"],
            )
            if progress.state != TaskProgressState.COMPLETED:
                raise RuntimeError("roadmap task did not complete")
            before = store.list_task_events(state_project.project_id, task.task_id)
            continuation = decide_exact_search_continuation(
                store,
                task_id=task.task_id,
                progress_decision_event_id=progress.decision_event_id,
            )
            after = store.list_task_events(state_project.project_id, task.task_id)
            if continuation.state != ContinuationState.COMPLETE_NO_ACTION:
                raise RuntimeError("completed task did not stop")
            if len(after) != len(before):
                raise RuntimeError("completed task created unnecessary continuation event")
            return "PASS", {
                "continuation_state": continuation.state.value,
                "extra_events": 0,
            }, 0, 0, 0

        scenario("S16", "Already complete -> stop, no extra action", s16)

        # S17 — donor license provenance remains attached to physical search evidence.
        def s17():
            execution = shared["s03_execution"]
            match = execution.verified_result["matches"][0]
            if match["trust_class"] != "donor_repo":
                raise RuntimeError("donor trust class lost")
            if match["license_state"] != "Apache-2.0":
                raise RuntimeError("donor license state lost")
            if match["repo_identity"] != "https://example.invalid/project-donor.git":
                raise RuntimeError("donor repo identity lost")
            return "PASS", {
                "trust_class": match["trust_class"],
                "license_state": match["license_state"],
                "repo_identity": match["repo_identity"],
            }, 0, 0, 0

        scenario("S17", "Donor provenance remains attached", s17)

        unexpected_failures = [item for item in results if item.status == "FAIL"]
        pass_count = sum(item.status == "PASS" for item in results)
        blocked_count = sum(item.status == "BLOCKED_EXPECTED" for item in results)
        total_model_calls = sum(item.model_calls for item in results)
        total_hand_calls = sum(item.hand_calls for item in results)
        total_cloud_calls = sum(item.cloud_calls for item in results)
        total_elapsed = round(sum(item.elapsed_seconds for item in results), 3)

        summary = {
            "schema": "orion.v3.usage-scenario-suite.v1",
            "run_id": "V3-USAGE-SUITE-001",
            "scenario_count": len(results),
            "pass_count": pass_count,
            "blocked_expected_count": blocked_count,
            "unexpected_fail_count": len(unexpected_failures),
            "model": MODEL,
            "thinking": "ON",
            "num_ctx": NUM_CTX,
            "model_calls": total_model_calls,
            "hand_calls": total_hand_calls,
            "cloud_calls": total_cloud_calls,
            "scenario_elapsed_seconds_sum": total_elapsed,
            "results": [asdict(item) for item in results],
        }
        print(
            "ORION_USAGE_SCENARIO_SUITE_SUMMARY> "
            + json.dumps(summary, ensure_ascii=False, sort_keys=True)
        )
        store.close()

    if unexpected_failures:
        print("ORION_USAGE_SCENARIO_SUITE_V1> FAIL")
        print("STATUS> FAIL")
        return 1

    print("ORION_USAGE_SCENARIO_SUITE_V1> PASS")
    print("STATUS> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
