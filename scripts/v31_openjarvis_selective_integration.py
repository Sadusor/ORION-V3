from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DONOR = ROOT / "external" / "OpenJarvis"
OPENJARVIS_SRC = DONOR / "src"
if not OPENJARVIS_SRC.exists():
    raise SystemExit("Pinned OpenJarvis donor is missing.")

sys.path.insert(0, str(OPENJARVIS_SRC))
sys.path.insert(0, str(ROOT / "src"))

import openjarvis.tools  # noqa: F401
import orion_v3.substrates.openjarvis_tools  # noqa: F401

from openjarvis.agents.simple import SimpleAgent
from openjarvis.core.events import EventBus, EventType
from openjarvis.core.types import ToolCall
from openjarvis.engine.ollama import OllamaEngine
from openjarvis.tools._stubs import ToolExecutor
from openjarvis.workflow.builder import WorkflowBuilder
from openjarvis.workflow.engine import WorkflowEngine

from orion_v3.authority import AuthorityGateway, LeaseAuthority
from orion_v3.substrates.openjarvis import (
    build_gate1_capability_policy,
    build_registered_filesystem_search_tool,
    normalize_filesystem_search_evidence,
)
from orion_v3.substrates.openjarvis_workflow import RecordingToolExecutor


print("V3_RUN_ID> V3-RUN-007")
print("OPENJARVIS_SELECTIVE_INTEGRATION> START")

# ---------------------------------------------------------------------------
# A. Deterministic OpenJarvis WorkflowEngine under ORION authority.
# ---------------------------------------------------------------------------

leases = LeaseAuthority()
gateway = AuthorityGateway(leases)
issued = leases.issue(
    task_id="V3-RUN-007",
    operation_id="filesystem.search",
    principal="owner",
    scope={
        "locations": ["project"],
        "recursive": True,
        "max_depth": 4,
        "max_results": 10,
    },
    ttl_seconds=90,
)

tool = build_registered_filesystem_search_tool(
    gateway,
    lease_token=issued.token,
    trusted_roots={"project": ROOT},
)

agent_id = "orion-v31-workflow-probe"
policy = build_gate1_capability_policy(agent_id)
donor_executor = ToolExecutor(
    [tool],
    capability_policy=policy,
    agent_id=agent_id,
)
recording_executor = RecordingToolExecutor(donor_executor)


class WorkflowSystem:
    def __init__(self, executor) -> None:
        self.tool_executor = executor


search_args = {
    "exact_names": ["pyproject.toml", "gateway.py"],
    "locations": ["project"],
    "recursive": True,
    "max_depth": 4,
    "max_results": 10,
}
graph = (
    WorkflowBuilder("orion_v3_readonly_search")
    .add_tool(
        "search_project",
        tool_name="orion_filesystem_search",
        tool_args=json.dumps(search_args),
    )
    .build()
)

workflow_result = WorkflowEngine().run(
    graph,
    WorkflowSystem(recording_executor),
)

assert workflow_result.success is True, workflow_result
assert len(workflow_result.steps) == 1, workflow_result.steps
assert len(recording_executor.records) == 1, recording_executor.records

record = recording_executor.records[0]
assert record.tool_name == "orion_filesystem_search"
assert record.result.success is True, record.result

evidence = normalize_filesystem_search_evidence(
    lease=issued.lease,
    tool_result=record.result,
)
paths = {item["relative_path"] for item in evidence.result["matches"]}
assert "pyproject.toml" in paths, paths
assert "src/orion_v3/authority/gateway.py" in paths, paths

# Donor WorkflowStepResult itself drops ToolResult.metadata. The ORION adapter
# must therefore remain the evidence tap unless upstream changes that contract.
assert workflow_result.steps[0].metadata == {}, workflow_result.steps[0].metadata

print("OPENJARVIS_WORKFLOW_ENGINE> EXECUTION_PASS")
print("WORKFLOW_AUTONOMOUS_AGENT_LOOP> NONE")
print("ORION_ACTION_LEASE> ENFORCED")
print("ORION_WORKFLOW_EVIDENCE_TAP> PASS")
print("DONOR_WORKFLOW_NATIVE_METADATA> DROPPED")
print("DONOR_WORKFLOW_DECISION> ADOPT_WITH_ORION_EVIDENCE_ADAPTER")

# ---------------------------------------------------------------------------
# B. One-call local router candidate: OpenJarvis SimpleAgent + Qwen3.5 9B.
# ---------------------------------------------------------------------------

engine = OllamaEngine(host="http://127.0.0.1:11434", timeout=90.0)
try:
    if not engine.health():
        raise RuntimeError("Ollama is not reachable on 127.0.0.1:11434")

    models = engine.list_models()
    preferred = "qwen3.5:9b"
    if preferred in models:
        model = preferred
    else:
        matches = [m for m in models if m.lower().startswith("qwen3.5:9b")]
        if not matches:
            raise RuntimeError(
                "qwen3.5:9b is not available in Ollama; discovered: "
                + ", ".join(models[:20])
            )
        model = matches[0]

    bus = EventBus(record_history=True)
    router = SimpleAgent(
        engine,
        model=model,
        bus=bus,
        temperature=0.0,
        max_tokens=8,
    )

    route_prompt = (
        "Choose exactly one workflow id for the request. "
        "Allowed ids: FILE_SEARCH or DIRECT_ANSWER. "
        "Reply with only the id, no explanation. "
        "Request: Find pyproject.toml and gateway.py in this project."
    )

    t0 = time.perf_counter()
    route_result = router.run(route_prompt)
    latency = time.perf_counter() - t0

    inference_events = [
        event
        for event in bus.history
        if event.event_type == EventType.INFERENCE_END
    ]
    assert len(inference_events) == 1, len(inference_events)
    usage = dict(inference_events[0].data.get("usage", {}) or {})

    raw_route = (route_result.content or "").strip()
    normalized_route = re.sub(r"[^A-Za-z_]", "", raw_route).upper()
    prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)
    completion_tokens = int(usage.get("completion_tokens", 0) or 0)
    total_tokens = int(
        usage.get("total_tokens", prompt_tokens + completion_tokens)
        or (prompt_tokens + completion_tokens)
    )

    assert route_result.turns == 1, route_result.turns
    assert not route_result.tool_results, route_result.tool_results
    assert normalized_route == "FILE_SEARCH", raw_route

    low_consumption_candidate = (
        total_tokens > 0
        and total_tokens <= 256
        and completion_tokens <= 8
    )

    print(f"OPENJARVIS_SIMPLE_MODEL> {model}")
    print("OPENJARVIS_SIMPLE_TURNS> 1")
    print("OPENJARVIS_SIMPLE_TOOL_CALLS> 0")
    print(f"OPENJARVIS_SIMPLE_ROUTE> {normalized_route}")
    print(f"OPENJARVIS_SIMPLE_PROMPT_TOKENS> {prompt_tokens}")
    print(f"OPENJARVIS_SIMPLE_COMPLETION_TOKENS> {completion_tokens}")
    print(f"OPENJARVIS_SIMPLE_TOTAL_TOKENS> {total_tokens}")
    print(f"OPENJARVIS_SIMPLE_LATENCY_MS> {latency * 1000.0:.1f}")
    print(
        "LOW_CONSUMPTION_ROUTER_CANDIDATE> "
        + ("PASS" if low_consumption_candidate else "TOO_EXPENSIVE")
    )
finally:
    engine.close()

print("OPENJARVIS_SELECTIVE_INTEGRATION> PASS")
print("STATUS> PASS")
