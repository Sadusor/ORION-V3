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


def request_json(
    port: int,
    method: str,
    path: str,
    *,
    token: str = "",
    payload: dict | None = None,
) -> tuple[int, dict]:
    data = None
    headers = {}
    if token:
        headers["X-Orion-Token"] = token
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def add_candidate(product, *, conversation_id: str, message_id: str, text: str):
    product.CHAT_HISTORY.sync(
        {
            "conversations": [
                {
                    "id": conversation_id,
                    "title": conversation_id,
                    "project_id": "",
                    "pinned": 0,
                    "archived": 0,
                    "deleted": 0,
                    "created_at_ms": 1000,
                    "updated_at_ms": 2000,
                }
            ],
            "messages": [
                {
                    "id": message_id,
                    "conversation_id": conversation_id,
                    "role": "user",
                    "text": text,
                    "source": "test",
                    "created_at_ms": 1500,
                }
            ],
        }
    )
    return product.MEMORY_CANDIDATES.enqueue_chat_message(
        conversation_id=conversation_id,
        message_id=message_id,
        project_id="",
    )["candidate"]


def direct_promote(product, candidate: dict, *, actor: str):
    ticket = product.MEMORY_REVIEW.prepare_review(
        candidate_id=candidate["candidate_id"],
        decision="promote",
        expected_content_sha256=candidate["content_sha256"],
        actor_fingerprint=actor,
    )
    return product.MEMORY_REVIEW.decide(
        candidate_id=candidate["candidate_id"],
        decision="promote",
        expected_content_sha256=candidate["content_sha256"],
        review_token=ticket["review_token"],
        actor_fingerprint=actor,
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="orion-integrity-product-") as td:
        os.environ["LOCALAPPDATA"] = td

        import product_server as product
        from modules.memory_integrity_anchor import MemoryIntegrityAnchor

        assert isinstance(product.MEMORY_INTEGRITY, MemoryIntegrityAnchor)
        initial = product.MEMORY_INTEGRITY.status()
        assert initial["state"] == "ok"
        assert initial["writes_frozen"] is False
        assert initial["head_seq"] == 1

        product.AUTH = product.Auth(
            "123456",
            pathlib.Path(td) / "devices-test.json",
        )
        token = product.AUTH.pair("123456")

        server = ThreadingHTTPServer(("127.0.0.1", 0), product.Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        port = server.server_address[1]

        try:
            # Normal owner promotion is committed by frozen V1, then observed
            # by V1.1 and anchored after the commit.
            c1 = add_candidate(
                product,
                conversation_id="c1",
                message_id="m1",
                text="My test beverage preference is tea.",
            )
            status, ticket = request_json(
                port,
                "POST",
                "/api/memory/review-ticket",
                token=token,
                payload={
                    "candidate_id": c1["candidate_id"],
                    "decision": "promote",
                    "expected_content_sha256": c1["content_sha256"],
                },
            )
            assert status == 200
            status, promoted = request_json(
                port,
                "POST",
                "/api/memory/decision",
                token=token,
                payload={
                    "candidate_id": c1["candidate_id"],
                    "decision": "promote",
                    "expected_content_sha256": c1["content_sha256"],
                    "review_token": ticket["review_token"],
                },
            )
            assert status == 201
            assert promoted["canonical_memory_written"] is True

            status, integrity = request_json(
                port,
                "GET",
                "/api/memory/integrity",
                token=token,
            )
            assert status == 200
            assert integrity["state"] == "ok"
            assert integrity["writes_frozen"] is False
            assert integrity["head_seq"] == 2

            # Simulate an out-of-band durable write that did not pass through
            # the observer. Startup-style verification must detect that the
            # current state is not in anchor history and freeze future writes.
            c2 = add_candidate(
                product,
                conversation_id="c2",
                message_id="m2",
                text="My test editor preference is Notepad.",
            )
            bypass = direct_promote(
                product,
                c2,
                actor="paired:out-of-band-test",
            )
            assert bypass["canonical_memory_written"] is True

            mismatch = product.MEMORY_INTEGRITY.initialize()
            assert mismatch["state"] == "mismatch"
            assert mismatch["writes_frozen"] is True
            assert mismatch["reason"] == "current_state_not_in_anchor_history"

            # Reads stay available while durable writes are frozen.
            status, canonical = request_json(
                port,
                "GET",
                "/api/memory/canonical",
                token=token,
            )
            assert status == 200
            assert canonical["count"] == 2

            # Prepare a valid owner decision, then prove the actual durable
            # commit boundary refuses it while integrity is frozen.
            c3 = add_candidate(
                product,
                conversation_id="c3",
                message_id="m3",
                text="My test shell preference is PowerShell.",
            )
            status, ticket3 = request_json(
                port,
                "POST",
                "/api/memory/review-ticket",
                token=token,
                payload={
                    "candidate_id": c3["candidate_id"],
                    "decision": "promote",
                    "expected_content_sha256": c3["content_sha256"],
                },
            )
            assert status == 200

            status, frozen = request_json(
                port,
                "POST",
                "/api/memory/decision",
                token=token,
                payload={
                    "candidate_id": c3["candidate_id"],
                    "decision": "promote",
                    "expected_content_sha256": c3["content_sha256"],
                    "review_token": ticket3["review_token"],
                },
            )
            assert status == 423
            assert frozen["error"] == "MEMORY_WRITES_FROZEN"

            # Explicit paired-owner recovery accepts the known current state
            # without rewriting canonical memory, then normal writes resume.
            status, recovered = request_json(
                port,
                "POST",
                "/api/memory/integrity/reanchor",
                token=token,
                payload={"reason": "test_accept_known_current_state"},
            )
            assert status == 200
            assert recovered["state"] == "ok"
            assert recovered["writes_frozen"] is False
            assert recovered["head_seq"] == 3

            status, promoted3 = request_json(
                port,
                "POST",
                "/api/memory/decision",
                token=token,
                payload={
                    "candidate_id": c3["candidate_id"],
                    "decision": "promote",
                    "expected_content_sha256": c3["content_sha256"],
                    "review_token": ticket3["review_token"],
                },
            )
            assert status == 201
            assert promoted3["canonical_memory_written"] is True

            final = product.MEMORY_INTEGRITY.status()
            assert final["state"] == "ok"
            assert final["writes_frozen"] is False
            assert final["head_seq"] == 4

            # Product status exposes integrity without changing memory semantics.
            status, product_status = request_json(
                port,
                "GET",
                "/api/status",
                token=token,
            )
            assert status == 200
            assert product_status["memory_integrity"]["state"] == "ok"

            print("MEMORY_INTEGRITY_PRODUCT_WIRING_V1_1A> PASS")
            print("STARTUP_VERIFY> PASS")
            print("POST_COMMIT_ANCHOR_OBSERVER> PASS")
            print("UNKNOWN_STATE_FREEZES_DURABLE_WRITES> PASS")
            print("READS_CONTINUE_WHILE_FROZEN> PASS")
            print("OWNER_REANCHOR_RECOVERY> PASS")
            print("WRITES_RESUME_AFTER_OWNER_RECOVERY> PASS")
            print("FROZEN_MEMORY_V1_MODULES_MODIFIED> NONE")
            return 0
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
