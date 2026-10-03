from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from openhands.sdk import Agent, Conversation, LLM, Tool
from openhands.sdk.conversation.response_utils import get_agent_final_response
from openhands.sdk.event import ActionEvent
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.terminal import TerminalTool
from pydantic import SecretStr


RESULT_START = "---ORION_COMPACT_CODING_HAND_RESULT_START---"
RESULT_END = "---ORION_COMPACT_CODING_HAND_RESULT_END---"

ORION_COMPACT_CODING_PROMPT = """You are a bounded Coding Hand inside ORION.
Follow the user's coding task literally and make the smallest correct change.
Use only the tools provided and only inside the disposable workspace.
Use native structured tool calls whenever a tool is needed; never print or imitate
tool-call syntax instead of calling the tool.
Use FileEditor for source-code edits. Use Terminal only for project-local inspection
or verification commands.
Do not commit, push, access the network, modify ORION authority/state, or act outside
the workspace. When the requested task is complete and verified, finish."""


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
    model = request.get("model", "ollama_chat/qwen3.6:35b-a3b")
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
    if model.startswith("ollama/"):
        model = "ollama_chat/" + model.removeprefix("ollama/")
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
    terminal_commands: list[str] = []

    def on_event(event) -> None:
        if isinstance(event, ActionEvent):
            tool_calls.append(str(event.tool_name))
            if event.tool_name == TerminalTool.name:
                command = getattr(getattr(event, "action", None), "command", None)
                terminal_commands.append(str(command))

    started = time.monotonic()
    conversation = None
    try:
        llm = LLM(
            usage_id="run-032-openhands-compact-coding",
            model=model,
            base_url=base_url,
            api_key=SecretStr("ollama"),
            reasoning_effort="none",
            temperature=0.0,
            num_retries=2,
            timeout=180,
            caching_prompt=False,
            native_tool_calling=True,
        )
        agent = Agent(
            llm=llm,
            tools=[
                Tool(name=FileEditorTool.name),
                Tool(name=TerminalTool.name),
            ],
            include_default_tools=["FinishTool"],
            system_prompt=ORION_COMPACT_CODING_PROMPT,
            system_prompt_kwargs={"cli_mode": True},
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

        system_events = [
            event
            for event in conversation.state.events
            if type(event).__name__ == "SystemPromptEvent"
        ]
        if not system_events:
            raise RuntimeError("Agent did not initialize a SystemPromptEvent")
        actual_system = str(system_events[-1].system_prompt.text)
        if actual_system != ORION_COMPACT_CODING_PROMPT:
            raise RuntimeError("compact ORION system prompt mismatch")

        conversation.run()
        final_content = get_agent_final_response(conversation.state.events)
        state = str(conversation.state.execution_status)
    except Exception as exc:
        emit(
            {
                "success": False,
                "error": type(exc).__name__,
                "detail": str(exc)[-2000:],
                "tool_calls": tool_calls,
                "terminal_commands": terminal_commands,
                "wall_seconds": round(time.monotonic() - started, 3),
                "model": model,
            }
        )
        return 1
    finally:
        if conversation is not None:
            conversation.close()

    emit(
        {
            "success": True,
            "model": model,
            "base_url": base_url,
            "system_prompt": "ORION_COMPACT_CODING_PROMPT",
            "tool_policy": [
                FileEditorTool.name,
                TerminalTool.name,
                "finish",
            ],
            "tool_calls": tool_calls,
            "terminal_commands": terminal_commands,
            "execution_status": state,
            "final_content": final_content[-4000:],
            "wall_seconds": round(time.monotonic() - started, 3),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
