from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile
import threading
import urllib.request
from http.server import ThreadingHTTPServer

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE.parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="orion-memory-product-") as td:
        # Isolate every product-server state file from the owner's live ORION.
        os.environ["LOCALAPPDATA"] = td

        import product_server as product

        product.CHAT_HISTORY.sync(
            {
                "conversations": [
                    {
                        "id": "old",
                        "title": "ORION model",
                        "project_id": "",
                        "pinned": 0,
                        "archived": 0,
                        "deleted": 0,
                        "created_at_ms": 1000,
                        "updated_at_ms": 2000,
                    },
                    {
                        "id": "current",
                        "title": "Current",
                        "project_id": "",
                        "pinned": 0,
                        "archived": 0,
                        "deleted": 0,
                        "created_at_ms": 3000,
                        "updated_at_ms": 3000,
                    },
                ],
                "messages": [
                    {
                        "id": "m-old",
                        "conversation_id": "old",
                        "role": "user",
                        "text": "The unique retrieval marker is NEBULA-417.",
                        "source": "test",
                        "created_at_ms": 2000,
                    },
                    {
                        "id": "m-current",
                        "conversation_id": "current",
                        "role": "user",
                        "text": "NEBULA-417 appears here too but current chat must be excluded.",
                        "source": "test",
                        "created_at_ms": 3000,
                    },
                ],
            }
        )

        product.AUTH = product.Auth("123456", pathlib.Path(td) / "devices.json")
        server = ThreadingHTTPServer(("127.0.0.1", 0), product.Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        port = server.server_address[1]

        try:
            url = (
                f"http://127.0.0.1:{port}/api/memory/search"
                "?q=NEBULA-417&conversation_id=current&limit=4"
            )
            with urllib.request.urlopen(url, timeout=3) as response:
                body = json.loads(response.read().decode("utf-8"))

            assert body["schema"] == "orion.memory-retrieval/1"
            assert body["trace"]["authority"] == "context_only"
            assert body["items"]
            ids = {x["provenance"]["message_id"] for x in body["items"]}
            assert "m-old" in ids
            assert "m-current" not in ids

            status_url = f"http://127.0.0.1:{port}/api/status"
            with urllib.request.urlopen(status_url, timeout=3) as response:
                status = json.loads(response.read().decode("utf-8"))
            assert status["memory_retrieval"]["schema"] == "orion.memory-retrieval/1"
            assert status["memory_retrieval"]["trace"]["selected_count"] >= 1
            assert status["local_hand_lane"]["brain_memory"]["authority"] == "context_only"

            print("ORION_MEMORY_PRODUCT_ROUTE> PASS")
            print("MEMORY_SEARCH_HTTP> PASS")
            print("STATUS_TRACE> PASS")
            print("LIVE_STATE_ISOLATION> PASS")
            return 0
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
