from __future__ import annotations

import json
import pathlib
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = pathlib.Path(__file__).resolve().parent
PARENT = HERE.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from brain_pipeline import BrainPipeline
from verifier_preflight import VerifierPreflightModule


class FakeVerifierHandler(BaseHTTPRequestHandler):
    mode = "pass"
    seen = None

    def log_message(self, fmt, *args):
        pass

    def _json(self, status: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/generate":
            self.send_error(404)
            return

        n = int(self.headers.get("Content-Length", "0") or 0)
        body = json.loads(self.rfile.read(n).decode("utf-8"))
        type(self).seen = body

        if type(self).mode == "pass":
            doc = {
                "ready": True,
                "reason": "Reply is bounded and does not claim unavailable evidence.",
                "unsupported_claims": [],
                "missing_evidence": [],
                "needs_escalation": False,
            }
        else:
            doc = {
                "ready": False,
                "reason": "Reply depends on evidence not available in the request.",
                "unsupported_claims": ["Unsupported external fact"],
                "missing_evidence": ["External evidence"],
                "needs_escalation": True,
            }

        self._json(
            200,
            {
                "response": json.dumps(doc),
                "done": True,
                "done_reason": "stop",
            },
        )


class FakeLocalBrain:
    def __init__(self, reply: str):
        self.reply = reply
        self.state = {
            "run_state": "idle",
            "result": "",
            "activity": "ready",
            "goal": "",
            "brain_state": "idle",
            "brain_phase": "idle",
            "brain_started_utc": "",
            "brain_model": "qwen3.5-9b-orion",
            "brain_conclusion": "",
            "brain_error": "",
            "brain_next_script": "",
            "brain_next_capability": "",
            "brain_preflight": "not-run",
            "brain_preflight_reason": "",
            "brain_quality_state": "not-run",
            "brain_quality_reason": "",
            "brain_quality_unsupported_claims": [],
            "brain_quality_missing_evidence": [],
            "brain_needs_escalation": False,
            "execution_kind": "",
            "execution_action": "",
        }

    def start(self, goal: str, model: str = "") -> dict:
        stamp = str(time.time_ns())
        self.state.update(
            {
                "goal": goal,
                "brain_state": "running",
                "brain_phase": "drafting",
                "brain_started_utc": stamp,
                "brain_model": model or "qwen3.5-9b-orion",
                "brain_conclusion": "",
            }
        )

        def finish():
            time.sleep(0.03)
            self.state.update(
                {
                    "brain_state": "ready",
                    "brain_phase": "complete",
                    "brain_conclusion": self.reply,
                }
            )

        threading.Thread(target=finish, daemon=True).start()
        return dict(self.state)

    def view(self) -> dict:
        return dict(self.state)

    def cached_models(self) -> list[str]:
        return ["qwen3.5-9b-orion"]

    def default_model(self) -> str:
        return "qwen3.5-9b-orion"


def wait_terminal(pipeline: BrainPipeline, timeout: float = 3.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        view = pipeline.view()
        if view["brain_state"] in {"ready", "blocked", "error"}:
            return view
        time.sleep(0.02)
    raise AssertionError("Verifier pipeline timed out")


def main() -> int:
    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeVerifierHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]

    try:
        verifier = VerifierPreflightModule(
            base_url=f"http://127.0.0.1:{port}"
        )

        safe = verifier.deterministic_preflight(
            "I can suggest the next engineering step. Nothing has been executed."
        )
        assert safe["allowed"] is True

        blocked = verifier.deterministic_preflight(
            "I opened Chrome and verified the page."
        )
        assert blocked["allowed"] is False

        pipeline = BrainPipeline(
            local_brain=FakeLocalBrain(
                "I can suggest a bounded next step. Nothing has been executed."
            ),
            verifier=verifier,
        )
        started = pipeline.start("Suggest one safe next step.")
        assert started["brain_state"] == "running"

        passed = wait_terminal(pipeline)
        assert passed["brain_state"] == "ready"
        assert passed["brain_preflight"] == "pass"
        assert passed["brain_quality_state"] == "pass"
        assert passed["brain_next_script"] == ""
        assert passed["brain_next_capability"] == ""
        assert passed["execution_kind"] == ""
        assert passed["execution_action"] == ""

        request = FakeVerifierHandler.seen
        assert request is not None
        assert request["model"] == "qwen3.5-9b-orion"
        assert request["think"] is False
        assert request["stream"] is False
        assert request["options"]["temperature"] == 0
        assert request["format"] == VerifierPreflightModule.SCHEMA

        pipeline2 = BrainPipeline(
            local_brain=FakeLocalBrain(
                "I opened Chrome and verified the page."
            ),
            verifier=verifier,
        )
        pipeline2.start("Tell me what you did.")
        deterministic_block = wait_terminal(pipeline2)
        assert deterministic_block["brain_state"] == "blocked"
        assert deterministic_block["brain_preflight"] == "blocked"
        assert deterministic_block["brain_quality_state"] == "not-run"

        FakeVerifierHandler.mode = "block"
        pipeline3 = BrainPipeline(
            local_brain=FakeLocalBrain(
                "A specific external claim is definitely true."
            ),
            verifier=verifier,
        )
        pipeline3.start("Give me a claim that requires external evidence.")
        semantic_block = wait_terminal(pipeline3)
        assert semantic_block["brain_state"] == "blocked"
        assert semantic_block["brain_preflight"] == "pass"
        assert semantic_block["brain_quality_state"] == "blocked"
        assert semantic_block["brain_needs_escalation"] is True

        print("ORION_VERIFIER_PREFLIGHT> PASS")
        print("DETERMINISTIC_PREFLIGHT> PASS")
        print("SEMANTIC_VERIFIER> PASS")
        print("FAIL_CLOSED> PASS")
        print("EXECUTION_AUTHORITY> NONE")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
