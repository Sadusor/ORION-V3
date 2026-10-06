from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE.parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def http_json(method: str, url: str, body: dict | None = None, token: str = ""):
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"} if data is not None else {}
    if token:
        headers["X-Orion-Token"] = token
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=4) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="orion-candidate-product-") as td:
        os.environ["LOCALAPPDATA"] = td

        import product_server as product

        product.CHAT_HISTORY.sync(
            {
                "conversations": [
                    {
                        "id": "source-chat",
                        "title": "Source",
                        "project_id": "",
                        "pinned": 0,
                        "archived": 0,
                        "deleted": 0,
                        "created_at_ms": 1000,
                        "updated_at_ms": 1000,
                    }
                ],
                "messages": [
                    {
                        "id": "source-message",
                        "conversation_id": "source-chat",
                        "role": "user",
                        "text": "Candidate exact source value is AMBER 55.",
                        "source": "test",
                        "created_at_ms": 1000,
                    }
                ],
            }
        )

        product.AUTH = product.Auth("123456", pathlib.Path(td) / "devices.json")
        server = ThreadingHTTPServer(("127.0.0.1", 0), product.Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{server.server_address[1]}"

        try:
            status, paired = http_json(
                "POST",
                base + "/api/pair",
                {"code": "123456"},
            )
            assert status == 200
            token = paired["token"]

            status, created = http_json(
                "POST",
                base + "/api/memory/candidate",
                {
                    "conversation_id": "source-chat",
                    "message_id": "source-message",
                    "project_id": "",
                    "owner_scope": "owner:primary",
                    # This field must be ignored. The server must snapshot the
                    # source message rather than trust arbitrary client text.
                    "content": "FORGED CLIENT CONTENT",
                },
                token,
            )
            assert status == 201
            assert created["ok"] is True
            assert created["created"] is True
            assert created["canonical_memory_written"] is False
            candidate = created["candidate"]
            assert candidate["content"] == "Candidate exact source value is AMBER 55."
            assert "FORGED" not in candidate["content"]
            assert candidate["decision"] == "pending"
            assert candidate["authority"] == "candidate_only"

            status, listed = http_json(
                "GET",
                base + "/api/memory/candidates",
                token=token,
            )
            assert status == 200
            assert listed["count"] == 1
            assert listed["candidates"][0]["candidate_id"] == candidate["candidate_id"]
            assert listed["canonical_memory_written"] is False

            status, duplicate = http_json(
                "POST",
                base + "/api/memory/candidate",
                {
                    "conversation_id": "source-chat",
                    "message_id": "source-message",
                    "project_id": "",
                },
                token,
            )
            assert status == 200
            assert duplicate["created"] is False

            status, rejected = http_json(
                "POST",
                base + "/api/memory/candidate",
                {
                    "conversation_id": "source-chat",
                    "message_id": "missing-message",
                    "project_id": "",
                },
                token,
            )
            assert status == 409
            assert rejected["ok"] is False

            print("ORION_MEMORY_CANDIDATE_HTTP> PASS")
            print("AUTHENTICATED_INTAKE> PASS")
            print("EXACT_SOURCE_SERVER_RESOLUTION> PASS")
            print("ARBITRARY_CLIENT_CONTENT_IGNORED> PASS")
            print("IDEMPOTENT_HTTP_DEDUPE> PASS")
            print("CANONICAL_MEMORY_WRITE> NONE")
            return 0
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
