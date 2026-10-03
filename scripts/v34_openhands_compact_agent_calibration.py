from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

from pydantic import SecretStr

from openhands.sdk import Agent, Conversation, LLM, Tool
from openhands.sdk.event import ActionEvent, AgentErrorEvent, MessageEvent, ObservationEvent
from openhands.sdk.llm import content_to_str
from openhands.tools.preset.default import register_default_tools
from openhands.tools.terminal import TerminalTool


MODEL = os.environ.get("ORION_CALIBRATION_MODEL", "ollama_chat/qwen3.6:35b-a3b")
OLLAMA_URL = "http://127.0.0.1:11434"
MARKER = "ORION_COMPACT_AGENT_CALIBRATION"
COMMAND = f"Write-Output {MARKER}"

ORION_COMPACT_PROMPT = """You are a bounded Coding Hand inside ORION.
Follow the user's bounded task literally.
Use only the tools provided to you and only inside the disposable workspace.
When a tool is needed, use the provider's native structured tool call. Never print,
imitate, or describe tool-call syntax instead of calling the tool.
Do not commit, push, access the network, modify ORION authority/state, or act outside
the workspace. After the requested task is complete, finish."""


def main() -> int:
    print("V3_RUN_ID> V3-RUN-031")
    print("OPENHANDS_COMPACT_AGENT_CALIBRATION> START")
    print("CALIBRATION_MODEL> " + MODEL)
    print("COMPACT_SYSTEM_PROMPT_LENGTH> " + str(len(ORION_COMPACT_PROMPT)))

    register_default_tools(enable_browser=False)

    with tempfile.TemporaryDirectory(prefix="orion-v3-run-031-") as td:
        conversation = None
        try:
            llm = LLM(
                usage_id="run-031-openhands-compact-agent",
                model=MODEL,
                base_url=OLLAMA_URL,
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
                tools=[Tool(name=TerminalTool.name)],
                include_default_tools=["FinishTool"],
                system_prompt=ORION_COMPACT_PROMPT,
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
                    item["text"] = "".join(
                        content_to_str(event.llm_message.content)
                    )[-1200:]
                elif isinstance(event, AgentErrorEvent):
                    item["error"] = str(event)[-1200:]
                elif isinstance(event, ObservationEvent):
                    item["observation"] = str(event)[-1600:]
                captured.append(item)

            conversation = Conversation(
                agent=agent,
                workspace=str(Path(td)),
                callbacks=[on_event],
                max_iteration_per_run=4,
                visualizer=None,
                delete_on_close=True,
            )

            prompt = (
                "Use the terminal tool exactly once to run this command: "
                + COMMAND
                + ". Then finish."
            )

            started = time.monotonic()
            conversation.send_message(prompt)

            system_events = [
                event for event in conversation.state.events
                if type(event).__name__ == "SystemPromptEvent"
            ]
            if not system_events:
                raise RuntimeError("Agent did not initialize a SystemPromptEvent")
            actual_system = str(system_events[-1].system_prompt.text)
            print("ACTUAL_SYSTEM_PROMPT_LENGTH> " + str(len(actual_system)))
            print(
                "CUSTOM_SYSTEM_PROMPT_EXACT> "
                + ("PASS" if actual_system == ORION_COMPACT_PROMPT else "FAIL")
            )
            if actual_system != ORION_COMPACT_PROMPT:
                print("STATUS> FAIL")
                return 1

            conversation.run()
            wall = time.monotonic() - started

            events = list(conversation.state.events)
            actions = [event for event in events if isinstance(event, ActionEvent)]
            terminal_actions = [
                event for event in actions if event.tool_name == TerminalTool.name
            ]
            observations = [
                event for event in events if isinstance(event, ObservationEvent)
            ]
            errors = [event for event in events if isinstance(event, AgentErrorEvent)]

            print("COMPACT_AGENT_WALL_SECONDS> " + f"{wall:.3f}")
            print("ACTION_EVENT_COUNT> " + str(len(actions)))
            print("TERMINAL_ACTION_COUNT> " + str(len(terminal_actions)))
            print("OBSERVATION_EVENT_COUNT> " + str(len(observations)))
            print("AGENT_ERROR_COUNT> " + str(len(errors)))

            for index, event in enumerate(terminal_actions):
                action = getattr(event, "action", None)
                command = getattr(action, "command", None)
                print(f"TERMINAL_ACTION_{index}_COMMAND> " + str(command))

            for index, item in enumerate(captured):
                print(
                    f"RAW_EVENT_{index}> "
                    + json.dumps(item, ensure_ascii=False, sort_keys=True)[:2400]
                )

            if errors:
                print("DIAGNOSIS> COMPACT_AGENT_ERROR")
                print("STATUS> FAIL")
                return 1

            if not terminal_actions:
                print("REAL_AGENT_STRUCTURED_TERMINAL_ACTION> FAIL")
                print("DIAGNOSIS> COMPACT_PROMPT_DID_NOT_RESTORE_AGENT_TOOL_CALLING")
                print("STATUS> FAIL")
                return 1

            print("REAL_AGENT_STRUCTURED_TERMINAL_ACTION> PASS")

            command_ok = any(
                MARKER in str(getattr(getattr(event, "action", None), "command", ""))
                for event in terminal_actions
            )
            print(
                "EXPECTED_TERMINAL_COMMAND> "
                + ("PASS" if command_ok else "FAIL")
            )
            if not command_ok:
                print("DIAGNOSIS> WRONG_TERMINAL_COMMAND")
                print("STATUS> FAIL")
                return 1

            observation_text = "\n".join(str(event) for event in observations)
            observation_ok = MARKER in observation_text
            print(
                "EXPECTED_TERMINAL_OBSERVATION> "
                + ("PASS" if observation_ok else "FAIL")
            )
            if not observation_ok:
                print("DIAGNOSIS> TERMINAL_ACTION_WITHOUT_EXPECTED_OBSERVATION")
                print("STATUS> FAIL")
                return 1

            print("DIAGNOSIS> COMPACT_ORION_PROMPT_RESTORES_FULL_AGENT_TOOL_PATH")
            print("OPENHANDS_COMPACT_AGENT_PATH> PASS")
            print("STATUS> PASS")
            return 0
        finally:
            if conversation is not None:
                conversation.close()


if __name__ == "__main__":
    raise SystemExit(main())
