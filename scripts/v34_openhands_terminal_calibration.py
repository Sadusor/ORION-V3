from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SDK = ROOT / "external" / "OpenHands-software-agent-sdk"

MODEL = os.environ.get("ORION_CALIBRATION_MODEL", "ollama/qwen3.6:35b-a3b")
OLLAMA_URL = "http://127.0.0.1:11434"


def ollama_tags() -> dict:
    with urllib.request.urlopen(OLLAMA_URL + "/api/tags", timeout=1.5) as response:
        return json.loads(response.read().decode("utf-8"))


def find_ollama() -> str | None:
    for candidate in (
        shutil.which("ollama.exe"),
        shutil.which("ollama"),
        str(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"),
        str(Path(os.environ.get("LOCALAPPDATA", "")) / "Ollama" / "ollama.exe"),
    ):
        if candidate and Path(candidate).is_file():
            return candidate
    return None


def ensure_ollama() -> dict:
    try:
        return ollama_tags()
    except Exception:
        executable = find_ollama()
        if not executable:
            raise RuntimeError("Ollama is not running and ollama.exe was not found")
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
        subprocess.Popen(
            [executable, "serve"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=flags,
        )
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                return ollama_tags()
            except Exception:
                time.sleep(0.25)
        raise RuntimeError("Ollama did not become ready")


def main() -> int:
    print("V3_RUN_ID> V3-RUN-024")
    print("OPENHANDS_TERMINAL_CALIBRATION> START")
    print("CALIBRATION_MODEL> " + MODEL)

    tags = ensure_ollama()
    names = {
        str(item.get("name") or "")
        for item in tags.get("models", [])
        if isinstance(item, dict)
    }
    local_name = MODEL.removeprefix("ollama_chat/").removeprefix("ollama/")
    if local_name not in names:
        print("LOCAL_MODEL_AVAILABLE> FAIL " + local_name)
        print("OLLAMA_INSTALLED_MODELS> " + ",".join(sorted(names)))
        print("STATUS> FAIL")
        return 1

    sys.path.insert(0, str(SDK / "openhands-sdk"))
    sys.path.insert(0, str(SDK / "openhands-tools"))

    from pydantic import SecretStr
    from openhands.sdk import Agent, Conversation, LLM, Tool
    from openhands.sdk.event import (
        ActionEvent,
        AgentErrorEvent,
        MessageEvent,
        ObservationEvent,
        SystemPromptEvent,
    )
    from openhands.sdk.llm import content_to_str
    from openhands.sdk.tool import list_registered_tools
    from openhands.tools.file_editor import FileEditorTool
    from openhands.tools.preset.default import register_default_tools
    from openhands.tools.terminal import TerminalTool

    # Donor-faithful registration path. In this pinned SDK the concrete tool
    # modules also auto-register on import; this call intentionally mirrors the
    # donor Ollama E2E example for calibration.
    register_default_tools(enable_browser=False)

    registered = set(list_registered_tools())
    if TerminalTool.name not in registered:
        raise RuntimeError("TerminalTool is not registered")
    if FileEditorTool.name not in registered:
        raise RuntimeError("FileEditorTool is not registered")

    print("TERMINAL_TOOL_REGISTERED> PASS")
    print("FILE_EDITOR_TOOL_REGISTERED> PASS")
    print("REGISTER_DEFAULT_TOOLS_REQUIRED_FOR_FILE_EDITOR> NO")
    print("AGENT_TOOL_POLICY> TERMINAL_ONLY")
    print("CALIBRATION_SCOPE> DISPOSABLE_SYNTHETIC_WORKSPACE")

    with tempfile.TemporaryDirectory(prefix="orion-v3-run-024-") as td:
        workspace = Path(td)
        src = workspace / "src"
        src.mkdir()
        expected = "ORION_TERMINAL_CALIBRATION\n"
        (src / "clamp.py").write_text(expected, encoding="utf-8")

        model = MODEL
        if model.startswith("ollama/"):
            model = "ollama_chat/" + model.removeprefix("ollama/")

        llm = LLM(
            usage_id="run-024-openhands-terminal",
            model=model,
            base_url=OLLAMA_URL,
            api_key=SecretStr("ollama"),
            reasoning_effort="none",
            temperature=0.0,
            num_retries=8,
            timeout=900,
            caching_prompt=False,
        )
        agent = Agent(
            llm=llm,
            tools=[Tool(name=TerminalTool.name)],
            system_prompt_kwargs={"cli_mode": True},
        )

        captured: list[dict] = []

        def on_event(event) -> None:
            item = {
                "type": type(event).__name__,
                "source": getattr(event, "source", None),
                "tool_name": getattr(event, "tool_name", None),
            }
            if isinstance(event, MessageEvent):
                item["text"] = "".join(content_to_str(event.llm_message.content))[-1200:]
            elif isinstance(event, AgentErrorEvent):
                item["error"] = str(event)[-1200:]
            elif isinstance(event, ObservationEvent):
                item["observation"] = str(event)[-1200:]
            elif isinstance(event, SystemPromptEvent):
                item["advertised_tools"] = [
                    getattr(tool, "name", type(tool).__name__) for tool in event.tools
                ]
            captured.append(item)

        conversation = Conversation(
            agent=agent,
            workspace=str(workspace),
            callbacks=[on_event],
            max_iteration_per_run=8,
            visualizer=None,
            delete_on_close=True,
        )

        command = "Get-Content src\\clamp.py"
        prompt = (
            "Use the available terminal tool. Run exactly this PowerShell command: "
            + command
            + ". Do not run any other command. Then finish."
        )

        started = time.monotonic()
        conversation.send_message(prompt)
        conversation.run()
        wall = time.monotonic() - started

        events = list(conversation.state.events)
        action_events = [event for event in events if isinstance(event, ActionEvent)]
        terminal_actions = [
            event for event in action_events if event.tool_name == TerminalTool.name
        ]
        message_events = [
            event for event in events
            if isinstance(event, MessageEvent) and getattr(event, "source", None) == "agent"
        ]
        error_events = [event for event in events if isinstance(event, AgentErrorEvent)]
        system_events = [event for event in events if isinstance(event, SystemPromptEvent)]

        advertised = []
        if system_events:
            advertised = [
                getattr(tool, "name", type(tool).__name__) for tool in system_events[-1].tools
            ]

        print("CALIBRATION_WALL_SECONDS> " + f"{wall:.3f}")
        print("RAW_EVENT_COUNT> " + str(len(events)))
        print("ACTION_EVENT_COUNT> " + str(len(action_events)))
        print("TERMINAL_ACTION_COUNT> " + str(len(terminal_actions)))
        print("AGENT_MESSAGE_COUNT> " + str(len(message_events)))
        print("AGENT_ERROR_COUNT> " + str(len(error_events)))
        print("SYSTEM_PROMPT_TOOLS> " + ",".join(advertised))

        for index, item in enumerate(captured):
            compact = json.dumps(item, ensure_ascii=False, sort_keys=True)
            print(f"RAW_EVENT_{index}> " + compact[:2000])

        if TerminalTool.name not in advertised:
            print("TERMINAL_SCHEMA_ADVERTISED> FAIL")
            print("DIAGNOSIS> OPENHANDS_TOOL_ADVERTISEMENT")
            print("STATUS> FAIL")
            conversation.close()
            return 1

        print("TERMINAL_SCHEMA_ADVERTISED> PASS")

        if not terminal_actions:
            print("TERMINAL_ACTION_EMITTED> FAIL")
            if message_events:
                last_text = "".join(content_to_str(message_events[-1].llm_message.content))
                print("LAST_AGENT_TEXT> " + last_text.replace("\n", " ")[-1600:])
                print("DIAGNOSIS> MODEL_OR_TRANSPORT_NO_STRUCTURED_TOOL_CALL")
            elif error_events:
                print("DIAGNOSIS> OPENHANDS_OR_PROVIDER_ERROR")
            else:
                print("DIAGNOSIS> NO_AGENT_ACTION_OR_MESSAGE")
            print("STATUS> FAIL")
            conversation.close()
            return 1

        print("TERMINAL_ACTION_EMITTED> PASS")
        observations = [
            event for event in events if isinstance(event, ObservationEvent)
        ]
        observation_text = "\n".join(str(event) for event in observations)
        if "ORION_TERMINAL_CALIBRATION" not in observation_text:
            print("TERMINAL_OBSERVATION> FAIL")
            print("DIAGNOSIS> TOOL_ACTION_WITHOUT_EXPECTED_OBSERVATION")
            print("STATUS> FAIL")
            conversation.close()
            return 1

        print("TERMINAL_OBSERVATION> PASS")
        print("DIAGNOSIS> OPENHANDS_TERMINAL_TOOL_PATH_HEALTHY")
        print("OPENHANDS_TERMINAL_CALIBRATION> PASS")
        print("STATUS> PASS")
        conversation.close()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
