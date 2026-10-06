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
    with tempfile.TemporaryDirectory(prefix="orion-review-product-") as td:
        os.environ["LOCALAPPDATA"] = td

        import product_server as product

        product.CHAT_HISTORY.sync(
            {
                "conversations": [
                    {
                        "id": "facts",
                        "title": "Facts",
                        "project_id": "",
                        "pinned": 0,
                        "archived": 0,
                        "deleted": 0,
                        "created_at_ms": 1000,
                        "updated_at_ms": 1200,
                    }
                ],
                "messages": [
                    {
                        "id": "green",
                        "conversation_id": "facts",
                        "role": "user",
                        "text": "The owner-confirmed value is GREEN 842.",
                        "source": "test",
                        "created_at_ms": 1100,
                    },
                    {
                        "id": "secret",
                        "conversation_id": "facts",
                        "role": "user",
                        "text": "password = do-not-store-this",
                        "source": "test",
                        "created_at_ms": 1200,
                    },
                ],
            }
        )

        product.AUTH = product.Auth("123456", pathlib.Path(td) / "devices.json")
        server = ThreadingHTTPServer(("127.0.0.1", 0), product.Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{server.server_address[1]}"

        try:
            status, paired = http_json("POST", base + "/api/pair", {"code": "123456"})
            assert status == 200
            token = paired["token"]

            status, queued = http_json(
                "POST",
                base + "/api/memory/candidate",
                {
                    "conversation_id": "facts",
                    "message_id": "green",
                    "project_id": "",
                },
                token,
            )
            assert status == 201
            candidate = queued["candidate"]

            status, before = http_json("GET", base + "/api/memory/candidates", token=token)
            assert status == 200
            assert before["pending_count"] == 1
            assert before["promoted_count"] == 0

            status, promoted = http_json(
                "POST",
                base + "/api/memory/decision",
                {
                    "candidate_id": candidate["candidate_id"],
                    "decision": "promote",
                    "expected_content_sha256": candidate["content_sha256"],
                    "owner_scope": "owner:primary",
                    "content": "FORGED CLIENT REPLACEMENT",
                },
                token,
            )
            assert status == 201
            assert promoted["canonical_memory_written"] is True
            memory = promoted["memory"]
            assert memory["content"] == "The owner-confirmed value is GREEN 842."
            assert "FORGED" not in memory["content"]
            assert memory["authority"] == "context_only"

            status, canonical = http_json("GET", base + "/api/memory/canonical", token=token)
            assert status == 200
            assert canonical["count"] == 1
            assert canonical["memories"][0]["memory_id"] == memory["memory_id"]

            status, after = http_json("GET", base + "/api/memory/candidates", token=token)
            assert status == 200
            assert after["pending_count"] == 0
            assert after["promoted_count"] == 1
            assert after["candidates"][0]["decision"] == "promote"

            status, repeated = http_json(
                "POST",
                base + "/api/memory/decision",
                {
                    "candidate_id": candidate["candidate_id"],
                    "decision": "promote",
                    "expected_content_sha256": candidate["content_sha256"],
                },
                token,
            )
            assert status == 200
            assert repeated["created"] is False
            assert repeated["memory"]["memory_id"] == memory["memory_id"]

            status, reversal = http_json(
                "POST",
                base + "/api/memory/decision",
                {
                    "candidate_id": candidate["candidate_id"],
                    "decision": "reject",
                    "expected_content_sha256": candidate["content_sha256"],
                },
                token,
            )
            assert status == 409
            assert "terminal" in reversal["error"]

            status, decisions = http_json("GET", base + "/api/memory/decisions", token=token)
            assert status == 200
            assert decisions["append_only"] is True
            assert decisions["count"] == 1

            status, secret_q = http_json(
                "POST",
                base + "/api/memory/candidate",
                {
                    "conversation_id": "facts",
                    "message_id": "secret",
                    "project_id": "",
                },
                token,
            )
            assert status == 201
            secret = secret_q["candidate"]

            status, denied = http_json(
                "POST",
                base + "/api/memory/decision",
                {
                    "candidate_id": secret["candidate_id"],
                    "decision": "promote",
                    "expected_content_sha256": secret["content_sha256"],
                },
                token,
            )
            assert status == 409
            assert "secret material" in denied["error"]

            status, rejected = http_json(
                "POST",
                base + "/api/memory/decision",
                {
                    "candidate_id": secret["candidate_id"],
                    "decision": "reject",
                    "expected_content_sha256": secret["content_sha256"],
                },
                token,
            )
            assert status == 201
            assert rejected["canonical_memory_written"] is False

            print("ORION_CANONICAL_MEMORY_REVIEW_HTTP> PASS")
            print("AUTHENTICATED_OWNER_DECISION> PASS")
            print("SERVER_SOURCE_BINDING> PASS")
            print("CANONICAL_READ_ROUTE> PASS")
            print("IDEMPOTENT_PROMOTION> PASS")
            print("TERMINAL_REVERSAL_DENIED> PASS")
            print("SECRET_PROMOTION_DENIED> PASS")
            print("DECISION_LOG_READ_ROUTE> PASS")
            print("CANONICAL_MEMORY_AUTHORITY> CONTEXT_ONLY")
            return 0
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
