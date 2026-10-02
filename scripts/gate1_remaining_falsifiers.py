from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Sequence

ROOT = Path(__file__).resolve().parents[1]
OPENJARVIS_SRC = ROOT / "external" / "OpenJarvis" / "src"
if not OPENJARVIS_SRC.exists():
    raise SystemExit("Pinned OpenJarvis donor is missing.")
sys.path.insert(0, str(OPENJARVIS_SRC))
sys.path.insert(0, str(ROOT / "src"))

from openjarvis.agents.native_react import NativeReActAgent
from openjarvis.core.types import Message, ToolCall, ToolResult
from openjarvis.engine._stubs import InferenceEngine
from openjarvis.security.capabilities import CapabilityPolicy
from openjarvis.tools._stubs import BaseTool, ToolExecutor, ToolSpec
from orion_v3.authority import AuthorityGateway, LeaseAuthority
from orion_v3.substrates.openjarvis import build_filesystem_search_tool


class ScriptedEngine(InferenceEngine):
    engine_id = "orion-gate1-scripted"
    is_cloud = False

    def __init__(self) -> None:
        self.calls = 0

    def generate(
        self,
        messages: Sequence[Message],
        *,
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        self.calls += 1
        if self.calls == 1:
            return {
                "content": (
                    "Thought: attempt native Jarvis tool execution\n"
                    "Action: orion_filesystem_search\n"
                    'Action Input: {"exact_names":["report.txt"],'
                    '"locations":["documents"],"recursive":true,'
                    '"max_depth":1,"max_results":2}'
                ),
                "usage": {},
                "finish_reason": "stop",
            }
        return {
            "content": "Thought: done\nFinal Answer: finished",
            "usage": {},
            "finish_reason": "stop",
        }

    async def stream(
        self,
        messages: Sequence[Message],
        *,
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        if False:
            yield ""

    def list_models(self) -> List[str]:
        return ["scripted"]

    def health(self) -> bool:
        return True


def native_agent_bypass_falsifier() -> None:
    calls = []

    def dispatcher(authorized):
        calls.append(authorized)
        return {"matches": []}

    leases = LeaseAuthority()
    gateway = AuthorityGateway(leases)

    # Deliberately unbound: Jarvis gets the tool, but ORION minted no authority.
    tool = build_filesystem_search_tool(gateway, dispatcher)

    # Deliberately permissive donor posture. This test asks whether Jarvis can
    # widen itself enough to bypass ORION. It must not.
    policy = CapabilityPolicy(default_deny=False)
    agent = NativeReActAgent(
        ScriptedEngine(),
        "scripted",
        tools=[tool],
        max_turns=2,
        temperature=0.0,
        capability_policy=policy,
        agent_id="native-react-bypass-probe",
    )
    result = agent.run("Search for report.txt in documents.")

    assert result.tool_results, result
    first = result.tool_results[0]
    assert first.success is False, first
    assert first.metadata.get("orion_denial_code") == "missing_action_lease", first
    assert calls == [], "Native Jarvis agent reached ORION dispatcher without a lease"

    print("NATIVE_AGENT_BYPASS=DENIED")
    print("JARVIS_POLICY_WIDENING=NO_ORION_AUTHORITY")


class BlockingTool(BaseTool):
    tool_id = "orion_gate1_blocking_thread_probe"
    is_local = True

    def __init__(self, started: threading.Event, finished: threading.Event) -> None:
        self.started = started
        self.finished = finished

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self.tool_id,
            description="Gate-1 timeout semantics probe.",
            timeout_seconds=0.10,
        )

    def execute(self, **params: Any) -> ToolResult:
        self.started.set()
        time.sleep(1.25)
        self.finished.set()
        return ToolResult(tool_name=self.tool_id, content="finished", success=True)


def donor_timeout_is_not_stop_falsifier() -> None:
    started = threading.Event()
    finished = threading.Event()
    tool = BlockingTool(started, finished)
    executor = ToolExecutor([tool], default_timeout=0.10)

    result = executor.execute(
        ToolCall(id="timeout-probe", name=tool.tool_id, arguments="{}")
    )

    assert started.is_set(), "Blocking donor tool never started"
    assert result.success is False, result
    assert not finished.is_set(), (
        "Probe completed before timeout; cannot prove donor timeout semantics"
    )

    # The crucial falsifier: after ToolExecutor has returned its timeout result,
    # the underlying Python function is still alive and later completes.
    if not finished.wait(2.5):
        raise AssertionError("Timed-out donor thread never completed during observation")
    print("DONOR_TIMEOUT_RETURNED_WHILE_WORK_CONTINUED=PASS")
    print("TIMEOUT_IS_NOT_STOP=PASS")


def _worker_source() -> str:
    return """from __future__ import annotations
import os
import sys
import time
from pathlib import Path

heartbeat = Path(sys.argv[1])
ready = Path(sys.argv[2])
ready.write_text(str(os.getpid()), encoding='ascii')
counter = 0
while True:
    counter += 1
    heartbeat.write_text(str(counter), encoding='ascii')
    time.sleep(0.10)
"""


def physical_stop_falsifier() -> None:
    with tempfile.TemporaryDirectory(prefix="orion-v3-stop-") as tmp:
        root = Path(tmp)
        worker = root / "worker.py"
        heartbeat = root / "heartbeat.txt"
        ready = root / "ready.txt"
        worker.write_text(_worker_source(), encoding="utf-8")

        proc = subprocess.Popen(
            [sys.executable, str(worker), str(heartbeat), str(ready)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

        try:
            deadline = time.monotonic() + 5.0
            while time.monotonic() < deadline:
                if ready.exists() and heartbeat.exists():
                    break
                time.sleep(0.05)
            else:
                raise AssertionError("Killable worker did not become ready")

            worker_pid = int(ready.read_text(encoding="ascii").strip())
            launcher_pid = proc.pid
            print(f"STOP_LAUNCHER_PID={launcher_pid}")
            print(f"STOP_WORKER_PID={worker_pid}")

            before = int(heartbeat.read_text(encoding="ascii").strip())
            time.sleep(0.25)
            active = int(heartbeat.read_text(encoding="ascii").strip())
            assert active > before, "Worker is not demonstrably running"

            # On Windows a Python/uv launcher may sit between Popen and the
            # actual interpreter. The worker-reported PID is therefore the
            # authority for Stop; never assume launcher PID == worker PID.
            killed = subprocess.run(
                ["taskkill", "/PID", str(worker_pid), "/T", "/F"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if killed.returncode != 0:
                raise AssertionError(
                    "taskkill failed for actual worker PID "
                    + str(worker_pid)
                    + ": "
                    + (killed.stderr or killed.stdout).strip()
                )

            deadline = time.monotonic() + 5.0
            worker_alive = True
            while time.monotonic() < deadline:
                listing = subprocess.run(
                    [
                        "tasklist",
                        "/FI",
                        f"PID eq {worker_pid}",
                        "/FO",
                        "CSV",
                        "/NH",
                    ],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                output = (listing.stdout or "").strip()
                worker_alive = str(worker_pid) in output and "No tasks are running" not in output
                if not worker_alive:
                    break
                time.sleep(0.05)

            assert not worker_alive, "Windows still reports actual worker PID alive"

            stopped_value = heartbeat.read_text(encoding="ascii").strip()
            time.sleep(0.40)
            after_value = heartbeat.read_text(encoding="ascii").strip()
            assert after_value == stopped_value, (
                "Heartbeat changed after Stop; underlying work continued"
            )

            # Reap/clean the launcher handle if it still exists. This is cleanup,
            # not the proof of Stop; worker PID + heartbeat are the proof.
            if proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=2.0)

            print("WORKER_PID_OS_ABSENT=PASS")
            print("UNDERLYING_WORK_GONE=PASS")
            print("PHYSICAL_STOP=PASS")
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=5.0)


def main() -> None:
    native_agent_bypass_falsifier()
    donor_timeout_is_not_stop_falsifier()
    physical_stop_falsifier()
    print("GATE1_REMAINING_FALSIFIERS=PASS")


if __name__ == "__main__":
    main()
