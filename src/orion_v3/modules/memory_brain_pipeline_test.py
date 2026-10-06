from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
PARENT = HERE.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from modules.memory_brain_pipeline import MemoryAwareBrainPipeline


class FakeLocalBrain:
    def _available_models(self):
        return ["qwen-test"]


class FakeBrain:
    def __init__(self):
        self.local_brain = FakeLocalBrain()
        self.started_goal = ""
        self.started_model = ""
        self.state = {
            "brain_started_utc": "stamp-1",
            "brain_state": "running",
            "goal": "",
        }

    def cached_models(self):
        return ["qwen-test"]

    def default_model(self):
        return "qwen-test"

    def start(self, goal, model=""):
        self.started_goal = goal
        self.started_model = model
        self.state = {
            "brain_started_utc": "stamp-1",
            "brain_state": "running",
            "goal": goal,
        }
        return dict(self.state)

    def view(self):
        return dict(self.state)


class FakeMemory:
    def __init__(self, fail=False):
        self.fail = fail

    def retrieve(self, query, **kwargs):
        if self.fail:
            raise RuntimeError("synthetic retrieval failure")
        return {
            "query": query,
            "items": [{
                "id": "chat:m1",
                "title": "Old chat",
                "preview": "Qwen 9B was preferred.",
                "score": 2.0,
                "layer": "L1",
                "provenance": {
                    "source": "chat_history",
                    "conversation_id": "old",
                    "message_id": "m1",
                },
            }],
            "trace": {"source": "chat_history", "authority": "context_only", "context_item_count": 1},
            "context": "ORION READ-ONLY MEMORY CONTEXT\n\n[M1] Qwen 9B was preferred.",
        }

    @staticmethod
    def compose_owner_request(goal, retrieval):
        return (
            retrieval["context"] + "\n\n<OWNER_CURRENT_MESSAGE>\n" +
            goal + "\n</OWNER_CURRENT_MESSAGE>"
        )


def main() -> int:
    brain = FakeBrain()
    wrapped = MemoryAwareBrainPipeline(brain=brain, memory=FakeMemory())

    started = wrapped.start(
        "Which model did we prefer?",
        "qwen-test",
        memory_query="preferred local model",
        conversation_id="current",
    )
    assert brain.started_model == "qwen-test"
    assert "<OWNER_CURRENT_MESSAGE>" in brain.started_goal
    assert "Which model did we prefer?" in brain.started_goal
    assert "Qwen 9B was preferred." in brain.started_goal
    assert started["goal"] == "Which model did we prefer?"
    assert started["brain_memory"]["state"] == "pass"
    assert started["brain_memory"]["authority"] == "context_only"
    assert started["brain_memory"]["count"] == 1
    assert started["brain_memory"]["context_count"] == 1
    assert started["brain_memory"]["items"][0]["provenance"]["message_id"] == "m1"

    failed_brain = FakeBrain()
    failed = MemoryAwareBrainPipeline(brain=failed_brain, memory=FakeMemory(fail=True))
    state = failed.start("Hello", "qwen-test")
    assert failed_brain.started_goal == "Hello", "Retrieval failure changed owner request"
    assert state["brain_memory"]["state"] == "error"
    assert "synthetic retrieval failure" in state["brain_memory"]["error"]

    print("ORION_MEMORY_BRAIN_PIPELINE> PASS")
    print("FROZEN_BRAIN_WRAPPED> PASS")
    print("OWNER_GOAL_PRESERVED> PASS")
    print("MEMORY_FAILURE_VISIBLE_NONFATAL> PASS")
    print("MEMORY_AUTHORITY> CONTEXT_ONLY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
