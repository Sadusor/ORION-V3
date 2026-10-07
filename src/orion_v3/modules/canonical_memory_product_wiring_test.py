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
        self.started_goal = ""
        self.started_model = ""
        self.counter = 0
        self.state = {
            "brain_started_utc": "",
            "brain_state": "idle",
            "goal": "",
            "brain_stream_preview": "",
            "brain_conclusion": "",
        }

    def cached_models(self):
        return ["qwen-test"]

    def default_model(self):
        return "qwen-test"

    def start(self, goal, model=""):
        self.counter += 1
        self.started_goal = goal
        self.started_model = model
        self.state = {
            "brain_started_utc": f"stamp-{self.counter}",
            "brain_state": "running",
            "goal": goal,
            "brain_stream_preview": "",
            "brain_conclusion": "",
        }
        return dict(self.state)

    def view(self):
        return dict(self.state)


def post_json(port: int, path: str, payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def promote(review, candidate: dict) -> dict:
    actor = "paired:product-wiring-test"
    prepared = review.prepare_review(
        candidate_id=candidate["candidate_id"],
        decision="promote",
        expected_content_sha256=candidate["content_sha256"],
        actor_fingerprint=actor,
    )
    return review.decide(
        candidate_id=candidate["candidate_id"],
        decision="promote",
        expected_content_sha256=candidate["content_sha256"],
        review_token=prepared["review_token"],
        actor_fingerprint=actor,
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="orion-canonical-product-wire-") as td:
        os.environ["LOCALAPPDATA"] = td

        import product_server as product
        from modules.canonical_memory_integration import CanonicalMemoryIntegratedBrainPipeline
        from modules.canonical_memory_retrieval_foundation import CanonicalMemoryRetrievalFoundation
        from modules.memory_historical_query import MemoryHistoricalQuery

        assert isinstance(product.LOCAL_BRAIN, CanonicalMemoryIntegratedBrainPipeline)
        assert isinstance(
            product.CANONICAL_MEMORY_RETRIEVAL,
            CanonicalMemoryRetrievalFoundation,
        )
        assert isinstance(product.MEMORY_HISTORY, MemoryHistoricalQuery)
        assert product.LOCAL_BRAIN.history is product.MEMORY_HISTORY

        product.CHAT_HISTORY.sync(
            {
                "conversations": [
                    {
                        "id": "durable-source",
                        "title": "Durable source",
                        "project_id": "p1",
                        "pinned": 0,
                        "archived": 0,
                        "deleted": 0,
                        "created_at_ms": 1000,
                        "updated_at_ms": 1400,
                    },
                    {
                        "id": "recall-source",
                        "title": "Recall source",
                        "project_id": "p1",
                        "pinned": 0,
                        "archived": 0,
                        "deleted": 0,
                        "created_at_ms": 1100,
                        "updated_at_ms": 1500,
                    },
                    {
                        "id": "current",
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
                        "id": "durable-green",
                        "conversation_id": "durable-source",
                        "role": "user",
                        "text": "The owner-approved STARLING durable marker is GREEN 842.",
                        "source": "test",
                        "created_at_ms": 1200,
                    },
                    {
                        "id": "recall-blue",
                        "conversation_id": "recall-source",
                        "role": "user",
                        "text": "An older STARLING conversation recall marker is BLUE 123.",
                        "source": "test",
                        "created_at_ms": 1300,
                    },
                    {
                        "id": "current-old",
                        "conversation_id": "current",
                        "role": "user",
                        "text": "Current-chat STARLING history must not enter cross-chat recall.",
                        "source": "test",
                        "created_at_ms": 1650,
                    },
                ],
            }
        )

        candidate = product.MEMORY_CANDIDATES.enqueue_chat_message(
            conversation_id="durable-source",
            message_id="durable-green",
            project_id="p1",
        )["candidate"]
        promoted = promote(product.MEMORY_REVIEW, candidate)
        assert promoted["canonical_memory_written"] is True

        fake_brain = FakeBrain()
        product.LOCAL_BRAIN.brain = fake_brain
        product.LOCAL_BRAIN.local_brain = fake_brain.local_brain

        product.AUTH = product.Auth("123456", pathlib.Path(td) / "devices-test.json")
        server = ThreadingHTTPServer(("127.0.0.1", 0), product.Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        port = server.server_address[1]

        try:
            current_context = (
                "user: Previous same-chat note about STARLING.\n"
                "assistant: Same-chat answer is context only."
            )
            latest_owner = "What do we know about the STARLING markers?"
            legacy_goal = (
                "Conversation context from the owner's local chat memory:\n"
                + current_context
                + "\n\nAnswer the latest user message in that context."
            )

            status, body = post_json(
                port,
                "/api/local-hand/draft",
                {
                    "goal": legacy_goal,
                    "model": "qwen-test",
                    "memory_query": latest_owner,
                    "conversation_id": "current",
                    "project_id": "p1",
                },
            )
            assert status == 202
            lane = body["local_hand_lane"]
            assert lane["goal"] == latest_owner
            memory = lane["brain_memory"]
            assert memory["authority"] == "context_only"
            assert memory["trace"]["owner_message_source"] == "legacy_phone_memory_query"
            assert memory["trace"]["legacy_phone_context_recognized"] is True
            assert memory["trace"]["block_order"] == [
                "current_conversation_context",
                "conversation_recall",
                "owner_approved_durable",
                "owner_current_message",
            ]

            prompt = fake_brain.started_goal
            assert "<ORION_CURRENT_CONVERSATION_CONTEXT" in prompt
            assert "<ORION_RECALL_CONTEXT" in prompt
            assert "<ORION_OWNER_APPROVED_DURABLE_CONTEXT" in prompt
            assert "GREEN 842" in prompt
            assert "BLUE 123" in prompt
            assert "Current-chat STARLING history must not enter cross-chat recall." not in prompt
            assert prompt.endswith(
                "<OWNER_CURRENT_MESSAGE>\n"
                + latest_owner
                + "\n</OWNER_CURRENT_MESSAGE>"
            )

            explicit_owner = "Use this exact current owner message."
            status2, body2 = post_json(
                port,
                "/api/local-hand/draft",
                {
                    "goal": legacy_goal,
                    "model": "qwen-test",
                    "memory_query": "STARLING",
                    "owner_message": explicit_owner,
                    "conversation_id": "current",
                    "project_id": "p1",
                },
            )
            assert status2 == 202
            assert body2["local_hand_lane"]["goal"] == explicit_owner
            assert body2["local_hand_lane"]["brain_memory"]["trace"]["owner_message_source"] == (
                "explicit_owner_message"
            )
            assert fake_brain.started_goal.endswith(
                "<OWNER_CURRENT_MESSAGE>\n"
                + explicit_owner
                + "\n</OWNER_CURRENT_MESSAGE>"
            )

            print("CANONICAL_MEMORY_PRODUCT_WIRING> PASS")
            print("PRODUCT_LOCAL_BRAIN_WRAPPER> PASS")
            print("ANDROID_OWNER_MESSAGE_ISOLATION_ROUTE> PASS")
            print("CURRENT_CONVERSATION_CONTEXT_ONLY> PASS")
            print("CONVERSATION_RECALL_BLOCK> PASS")
            print("OWNER_APPROVED_DURABLE_BLOCK> PASS")
            print("CURRENT_CONVERSATION_EXCLUSION> PASS")
            print("OWNER_CURRENT_MESSAGE_LAST> PASS")
            print("LIVE_QWEN_CALL> NOT_RUN_IN_THIS_GATE")
            return 0
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
