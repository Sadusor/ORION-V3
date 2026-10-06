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

from modules.streaming_local_brain import StreamingLocalBrainModule


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
                {"models": [{"name": "qwen3.5-9b-orion"}]},
            )
        self.send_error(404)

    def do_POST(self):
        if self.path != "/api/generate":
            self.send_error(404)
            return

        n = int(self.headers.get("Content-Length", "0") or 0)
        body = json.loads(self.rfile.read(n).decode("utf-8"))
        type(self).last_generate = body

        events = [
            {"response": "I am ", "done": False},
            {"response": "qwen3.5-9b-orion ", "done": False},
            {"response": "running locally inside ORION.", "done": True},
        ]
        raw = "".join(json.dumps(x) + "\n" for x in events).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()

        first = (json.dumps(events[0]) + "\n").encode("utf-8")
        self.wfile.write(first)
        self.wfile.flush()
        time.sleep(0.12)

        rest = "".join(json.dumps(x) + "\n" for x in events[1:]).encode("utf-8")
        self.wfile.write(rest)
        self.wfile.flush()


def main() -> int:
    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeOllamaHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]

    try:
        module = StreamingLocalBrainModule(
            base_url=f"http://127.0.0.1:{port}"
        )
        started = module.start("What model do you use?")
        assert started["brain_state"] == "running"
        assert started["brain_stream_preview"] == ""

        deadline = time.time() + 2
        saw_live = False
        while time.time() < deadline:
            view = module.view()
            if view["brain_state"] == "running" and view["brain_stream_preview"]:
                saw_live = True
                assert view["brain_stream_preview"].startswith("I am ")
                break
            time.sleep(0.01)
        assert saw_live, "stream preview never became visible while running"

        deadline = time.time() + 2
        while time.time() < deadline:
            view = module.view()
            if view["brain_state"] == "ready":
                break
            time.sleep(0.01)
        else:
            raise AssertionError("streaming Local Brain did not finish")

        assert view["brain_conclusion"] == (
            "I am qwen3.5-9b-orion running locally inside ORION."
        )
        assert view["brain_stream_preview"] == view["brain_conclusion"]
        assert view["brain_next_script"] == ""
        assert view["brain_next_capability"] == ""
        assert view["execution_kind"] == ""

        request = FakeOllamaHandler.last_generate
        assert request is not None
        assert request["model"] == "qwen3.5-9b-orion"
        assert request["stream"] is True
        assert request["think"] is False
        assert "format" not in request
        assert "qwen3.5-9b-orion" in request["prompt"]
        assert "running locally inside ORION" in request["prompt"]

        print("ORION_STREAMING_LOCAL_BRAIN> PASS")
        print("LIVE_PREVIEW> PASS")
        print("MODEL_IDENTITY_GROUNDING> PASS")
        print("EXECUTION_AUTHORITY> NONE")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
