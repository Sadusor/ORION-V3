from __future__ import annotations

import json
import pathlib
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from local_brain import LocalBrainError, LocalBrainModule


class FakeOllamaHandler(BaseHTTPRequestHandler):
    last_generate = None

    def log_message(self, fmt, *args):
        pass

    def _json(self, status: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/tags":
            return self._json(
                200,
                {
                    "models": [
                        {"name": "other-model:latest"},
                        {"name": "qwen3.5-9b-orion"},
                    ]
                },
            )
        self.send_error(404)

    def do_POST(self):
        if self.path != "/api/generate":
            self.send_error(404)
            return

        n = int(self.headers.get("Content-Length", "0") or 0)
        body = json.loads(self.rfile.read(n).decode("utf-8"))
        type(self).last_generate = body

        response = {
            "conclusion": "I can help plan this request, but nothing has been executed.",
            "draft": "First inspect the relevant evidence, then propose the smallest bounded next action.",
        }
        self._json(
            200,
            {
                "model": body.get("model"),
                "response": json.dumps(response),
                "done": True,
                "done_reason": "stop",
                "prompt_eval_count": 42,
                "eval_count": 24,
            },
        )


def wait_done(module: LocalBrainModule, timeout: float = 3.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        view = module.view()
        if view["brain_state"] != "running":
            return view
        time.sleep(0.02)
    raise AssertionError("Local Brain test timed out")


def main() -> int:
    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeOllamaHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]

    try:
        module = LocalBrainModule(base_url=f"http://127.0.0.1:{port}")
        started = module.start("Explain the safest next engineering step.")
        assert started["brain_state"] == "running"
        assert started["brain_model"] == "qwen3.5-9b-orion"
        assert started["execution_kind"] == ""
        assert started["brain_next_script"] == ""
        assert started["brain_next_capability"] == ""

        done = wait_done(module)
        assert done["brain_state"] == "ready"
        assert done["brain_phase"] == "complete"
        assert "nothing has been executed" in done["brain_conclusion"]
        assert "Draft:" in done["brain_conclusion"]
        assert done["brain_preflight"] == "not-run"
        assert done["brain_quality_state"] == "not-run"
        assert done["execution_kind"] == ""
        assert done["execution_action"] == ""
        assert done["brain_next_script"] == ""
        assert done["brain_next_capability"] == ""

        request = FakeOllamaHandler.last_generate
        assert request is not None
        assert request["model"] == "qwen3.5-9b-orion"
        assert request["think"] is False
        assert request["stream"] is False
        assert request["options"]["temperature"] == 0
        assert request["format"] == LocalBrainModule.SCHEMA
        assert "tools" not in request

        try:
            module.start("test", model="missing-model")
            raise AssertionError("Unavailable model was accepted")
        except LocalBrainError as exc:
            assert "not available" in str(exc)

        try:
            LocalBrainModule(base_url="http://192.168.1.99:11434")
            raise AssertionError("Non-loopback Local Brain endpoint was accepted")
        except LocalBrainError as exc:
            assert "loopback" in str(exc).lower()

        print("ORION_LOCAL_BRAIN_MODULE> PASS")
        print("MODEL_SELECTION> PASS | qwen3.5-9b-orion")
        print("REASONING_ONLY> PASS | no script/capability/execution")
        print("LOOPBACK_ONLY> PASS")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
