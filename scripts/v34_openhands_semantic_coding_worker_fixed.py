from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from openhands.sdk import Agent, Conversation, LLM, Tool
from openhands.sdk.conversation.response_utils import get_agent_final_response
from openhands.sdk.event import ActionEvent
from openhands.tools.file_editor import FileEditorTool
from pydantic import SecretStr


RESULT_START = "---ORION_SEMANTIC_HAND_RESULT_START---"
RESULT_END = "---ORION_SEMANTIC_HAND_RESULT_END---"


def emit(payload: dict) -> None:
    print(RESULT_START)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    print(RESULT_END)


def main() -> int:
    try:
        request = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        emit({"success": False, "error": "invalid_json"})
        return 2

    workspace_raw = request.get("workspace")
    prompt = request.get("prompt")
    model = request.get("model", "ollama_chat/qwen3.5:9b")
    base_url = request.get("base_url", "http://127.0.0.1:11434")
    max_iterations = int(request.get("max_iterations", 8))

    if not isinstance(workspace_raw, str) or not workspace_raw:
        emit({"success": False, "error": "invalid_workspace"})
        return 2
    if not isinstance(prompt, str) or not prompt.strip():
        emit({"success": False, "error": "invalid_prompt"})
        return 2
    if not isinstance(model, str) or not model.strip():
        emit({"success": False, "error": "invalid_model"})
        return 2
    if not isinstance(base_url, str) or not base_url.startswith(
        ("http://127.0.0.1:", "http://localhost:")
    ):
        emit({"success": False, "error": "non_local_model_endpoint"})
        return 2
    if max_iterations < 1 or max_iterations > 12:
        emit({"success": False, "error": "invalid_iteration_limit"})
        return 2

    workspace = Path(workspace_raw).resolve()
    if not workspace.is_dir():
        emit({"success": False, "error": "workspace_missing"})
        return 2

    tool_calls: list[str] = []

    def on_event(event) -> None:
        if isinstance(event, ActionEvent):
            tool_calls.append(str(event.tool_name))

    started = time.monotonic()
    try:
        llm = LLM(
            model=model,
            base_url=base_url,
            temperature=0.0,
            timeout=90,
            caching_prompt=False,
        )
        agent = Agent(
            llm=llm,
            tools=[Tool(name=FileEditorTool.name)],
        )
        conversation = Conversation(
            agent=agent,
            workspace=str(workspace),
            callbacks=[on_event],
            max_iteration_per_run=max_iterations,
            visualizer=None,
            delete_on_close=True,
        )
        conversation.send_message(prompt)
        conversation.run()
        final_content = get_agent_final_response(conversation.state.events)
        state = str(conversation.state.execution_status)
        conversation.close()
    except Exception as exc:
        emit(
            {
                "success": False,
                "error": type(exc).__name__,
                "detail": str(exc)[-2000:],
                "tool_calls": tool_calls,
                "wall_seconds": round(time.monotonic() - started, 3),
                "model": model,
            }
        )
        return 1

    emit(
        {
            "success": True,
            "model": model,
            "base_url": base_url,
            "tool_policy": [FileEditorTool.name],
            "tool_calls": tool_calls,
            "execution_status": state,
            "final_content": final_content[-4000:],
            "wall_seconds": round(time.monotonic() - started, 3),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
