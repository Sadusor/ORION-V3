from __future__ import annotations

from dataclasses import dataclass

from orion_v3.substrates.openjarvis_workflow import RecordingToolExecutor


@dataclass
class FakeCall:
    id: str
    name: str
    arguments: str


@dataclass
class FakeResult:
    success: bool
    content: str
    metadata: dict


class FakeExecutor:
    def __init__(self) -> None:
        self.calls = []

    def execute(self, call):
        self.calls.append(call)
        return FakeResult(
            success=True,
            content="ok",
            metadata={"lease_id": "lease-1", "evidence": {"value": 7}},
        )

    def get_openai_tools(self):
        return [{"type": "function", "function": {"name": "fake"}}]


def test_recording_executor_is_transparent_and_preserves_metadata():
    inner = FakeExecutor()
    wrapped = RecordingToolExecutor(inner)
    call = FakeCall(id="call-1", name="fake", arguments='{"x": 1}')

    result = wrapped.execute(call)

    assert result is wrapped.records[0].result
    assert inner.calls == [call]
    assert wrapped.records[0].call_id == "call-1"
    assert wrapped.records[0].tool_name == "fake"
    assert wrapped.records[0].arguments == '{"x": 1}'
    assert wrapped.records[0].result.metadata["lease_id"] == "lease-1"
    assert wrapped.records[0].result.metadata["evidence"]["value"] == 7


def test_recording_executor_delegates_tool_descriptions():
    inner = FakeExecutor()
    wrapped = RecordingToolExecutor(inner)

    assert wrapped.get_openai_tools() == inner.get_openai_tools()


def test_records_returns_copy():
    wrapped = RecordingToolExecutor(FakeExecutor())
    wrapped.execute(FakeCall(id="a", name="fake", arguments="{}"))

    snapshot = wrapped.records
    snapshot.clear()

    assert len(wrapped.records) == 1
