from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any


@dataclass(frozen=True)
class RecordedToolExecution:
    """One donor ToolExecutor dispatch captured at the ORION boundary."""

    call_id: str
    tool_name: str
    arguments: str
    result: Any


class RecordingToolExecutor:
    """Transparent evidence tap around an OpenJarvis ToolExecutor.

    OpenJarvis WorkflowEngine currently stores only text output in
    WorkflowStepResult and drops ToolResult.metadata. ORION must retain the
    original ToolResult so lease identity and structured evidence can still be
    verified after a workflow step completes.

    This adapter does not authorize anything and does not widen donor
    permissions. The wrapped ToolExecutor and the ORION-bound tool remain
    responsible for their existing gates.
    """

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self._lock = Lock()
        self._records: list[RecordedToolExecution] = []

    def execute(self, tool_call: Any) -> Any:
        result = self._inner.execute(tool_call)
        record = RecordedToolExecution(
            call_id=str(getattr(tool_call, "id", "")),
            tool_name=str(getattr(tool_call, "name", "")),
            arguments=str(getattr(tool_call, "arguments", "")),
            result=result,
        )
        with self._lock:
            self._records.append(record)
        return result

    def get_openai_tools(self) -> Any:
        """Preserve the wrapped executor interface for future donor reuse."""

        return self._inner.get_openai_tools()

    @property
    def records(self) -> list[RecordedToolExecution]:
        with self._lock:
            return list(self._records)


__all__ = ["RecordedToolExecution", "RecordingToolExecutor"]
