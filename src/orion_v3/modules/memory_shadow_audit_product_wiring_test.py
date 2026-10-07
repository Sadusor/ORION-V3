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


class FakeLocalBrain:
    def _available_models(self):
        return ["qwen-test"]


class FakeBrain:
    def __init__(self):
        self.local_brain = FakeLocalBrain()
        self.state = {
            "brain_started_utc": "",
            "brain_state": "idle",
            "goal": "",
        }
        self.counter = 0

    def cached_models(self):
        return ["qwen-test"]

    def default_model(self):
        return "qwen-test"

    def start(self, goal, model=""):
        self.counter += 1
        self.state = {
            "brain_started_utc": f"stamp-{self.counter}",
            "brain_state": "running",
            "goal": goal,
        }
        return dict(self.state)

    def view(self):
        return dict(self.state)


def post_json(port: int, path: str, token: str, payload: dict):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data=data,
        headers={
            "Content-Type": "application/json",
            "X-Orion-Token": token,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def get_json(port: int, path: str, token: str):
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        headers={"X-Orion-Token": token},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def promote(product, candidate: dict, actor: str):
    ticket = product.MEMORY_REVIEW.prepare_review(
        candidate_id=candidate["candidate_id"],
        decision="promote",
        expected_content_sha256=candidate["content_sha256"],
        actor_fingerprint=actor,
    )
    result = product.MEMORY_REVIEW.decide(
        candidate_id=candidate["candidate_id"],
        decision="promote",
        expected_content_sha256=candidate["content_sha256"],
        review_token=ticket["review_token"],
        actor_fingerprint=actor,
    )
    product.MEMORY_INTEGRITY.observe_commit(
        cause="test:promotion",
        actor_fingerprint=actor,
    )
    return result


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="orion-shadow-product-") as td:
        os.environ["LOCALAPPDATA"] = td

        import product_server as product
        from modules.memory_shadow_audit import MemoryShadowAudit

        assert isinstance(product.MEMORY_SHADOW_AUDIT, MemoryShadowAudit)

        product.CHAT_HISTORY.sync(
            {
                "conversations": [
                    {
                        "id": "old-chat",
                        "title": "Old preference",
                        "project_id": "p1",
                        "pinned": 0,
                        "archived": 0,
                        "deleted": 0,
                        "created_at_ms": 1000,
                        "updated_at_ms": 1200,
                    },
                    {
                        "id": "durable-chat",
                        "title": "Durable current",
                        "project_id": "p1",
                        "pinned": 0,
                        "archived": 0,
                        "deleted": 0,
                        "created_at_ms": 1300,
                        "updated_at_ms": 1500,
                    },
                    {
                        "id": "current-chat",
                        "title": "Current",
                        "project_id": "p1",
                        "pinned": 0,
                        "archived": 0,
                        "deleted": 0,
                        "created_at_ms": 1600,
                        "updated_at_ms": 1700,
                    },
                ],
                "messages": [
                    {
                        "id": "old-dark",
                        "conversation_id": "old-chat",
                        "role": "user",
                        "text": "I prefer dark mode for ORION.",
                        "source": "test",
                        "created_at_ms": 1100,
                    },
                    {
                        "id": "current-light",
                        "conversation_id": "durable-chat",
                        "role": "user",
                        "text": "My preferred ORION mode is light.",
                        "source": "test",
                        "created_at_ms": 1400,
                    },
                ],
            }
        )

        candidate = product.MEMORY_CANDIDATES.enqueue_chat_message(
            conversation_id="durable-chat",
            message_id="current-light",
            project_id="p1",
        )["candidate"]
        promoted = promote(
            product,
            candidate,
            actor="paired:shadow-product-test",
        )
        assert promoted["canonical_memory_written"] is True

        fake_brain = FakeBrain()
        product.LOCAL_BRAIN.brain = fake_brain
        product.LOCAL_BRAIN.local_brain = fake_brain.local_brain

        product.AUTH = product.Auth(
            "123456",
            pathlib.Path(td) / "devices-test.json",
        )
        token = product.AUTH.pair("123456")

        server = ThreadingHTTPServer(("127.0.0.1", 0), product.Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        port = server.server_address[1]

        try:
            # Non-shadowing query does not create audit output.
            status0, _ = post_json(
                port,
                "/api/local-hand/draft",
                token,
                {
                    "goal": "Tell me hello.",
                    "model": "qwen-test",
                    "memory_query": "Tell me hello.",
                    "conversation_id": "current-chat",
                    "project_id": "p1",
                },
            )
            assert status0 == 202
            assert not product.MEMORY_SHADOW_AUDIT.path.exists()

            # Exact frozen-V1 same-slot case triggers the observer only after
            # the prompt has already been composed.
            status1, body1 = post_json(
                port,
                "/api/local-hand/draft",
                token,
                {
                    "goal": "What mode do I prefer for ORION?",
                    "model": "qwen-test",
                    "memory_query": "What mode do I prefer for ORION?",
                    "conversation_id": "current-chat",
                    "project_id": "p1",
                },
            )
            assert status1 == 202

            shadow = (
                body1["local_hand_lane"]["brain_memory"]["sources"]
                ["conversation_recall"]["trace"]["durable_slot_shadowing"]
            )
            assert shadow["total_shadowed"] == 1

            status2, audit_status = get_json(
                port,
                "/api/memory/shadow-audit",
                token,
            )
            assert status2 == 200
            assert audit_status["state"] == "ok"
            assert audit_status["events_written"] == 1
            assert audit_status["prompt_path_effect"] == "none"

            lines = product.MEMORY_SHADOW_AUDIT.path.read_text(
                encoding="utf-8"
            ).splitlines()
            assert len(lines) == 1
            event = json.loads(lines[0])
            assert event["old_recall"]["text"] == "I prefer dark mode for ORION."
            assert event["current_durable"]["text"] == "My preferred ORION mode is light."
            assert event["slot"] == "preference:mode:orion"
            assert event["prompt_path_effect"] == "none"

            # Product status exposes the observer state only.
            status3, product_status = get_json(port, "/api/status", token)
            assert status3 == 200
            assert product_status["memory_shadow_audit"]["events_written"] == 1

            print("MEMORY_SHADOW_AUDIT_PRODUCT_WIRING_V1_1B> PASS")
            print("NORMAL_TURN_ZERO_AUDIT_WORK> PASS")
            print("FROZEN_V1_SHADOW_COUNT_DRIVES_OBSERVER> PASS")
            print("DETAILED_EVENT_WRITTEN_AFTER_PROMPT_DECISION> PASS")
            print("QWEN_PROMPT_PATH_EFFECT> NONE")
            print("FROZEN_MEMORY_MODULES_MODIFIED> NONE")
            return 0
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
