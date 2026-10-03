from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

from pydantic import SecretStr

from openhands.sdk import Agent, Conversation, LLM, Message, Tool
from openhands.sdk.agent.utils import prepare_llm_messages
from openhands.sdk.llm import TextContent
from openhands.tools.preset.default import register_default_tools
from openhands.tools.terminal import TerminalTool


MODEL = os.environ.get("ORION_CALIBRATION_MODEL", "ollama_chat/qwen3.6:35b-a3b")
OLLAMA_URL = "http://127.0.0.1:11434"
COMMAND = "Write-Output ORION_AGENT_MESSAGE_ISOLATION"


def text_of(message: Message) -> str:
    return "".join(
        item.text for item in message.content if isinstance(item, TextContent)
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def classify(label: str, response) -> tuple[bool, str]:
    message = response.message
    calls = list(message.tool_calls or [])
    text = text_of(message)
    print(f"{label}_TOOL_CALL_COUNT> {len(calls)}")
    print(f"{label}_TEXT_LENGTH> {len(text)}")
    if text:
        print(f"{label}_TEXT> " + text[-1800:].replace("\n", " "))
    if calls:
        call = calls[0]
        print(f"{label}_TOOL_NAME> {call.name}")
        print(
            f"{label}_TOOL_ARGUMENTS> "
            + json.dumps(call.arguments, ensure_ascii=False, sort_keys=True, default=str)
        )
    ok = bool(calls) and calls[0].name == TerminalTool.name
    print(f"{label}_STRUCTURED_TOOL_CALL> " + ("PASS" if ok else "FAIL"))
    return ok, text


def describe_messages(label: str, messages: list[Message]) -> None:
    print(f"{label}_MESSAGE_COUNT> {len(messages)}")
    for index, message in enumerate(messages):
        text = text_of(message)
        lowered = text.lower()
        print(
            f"{label}_MESSAGE_{index}> role={message.role} "
            f"length={len(text)} sha256={sha256_text(text)} "
            f"invoke={'<invoke' in lowered} "
            f"function_tag={'<function=' in lowered} "
            f"xml={'xml' in lowered} "
            f"tool_word={'tool' in lowered}"
        )
        for needle in ("<invoke", "<function=", "tool", "function call", "xml"):
            pos = lowered.find(needle)
            if pos >= 0:
                snippet = text[max(0, pos - 180): pos + 420].replace("\n", " ")
                print(
                    f"{label}_MESSAGE_{index}_{needle.upper().replace(' ', '_')}_SNIPPET> "
                    + snippet
                )


def main() -> int:
    print("V3_RUN_ID> V3-RUN-028")
    print("OPENHANDS_AGENT_MESSAGE_ISOLATION> START")
    print("CALIBRATION_MODEL> " + MODEL)

    register_default_tools(enable_browser=False)

    with tempfile.TemporaryDirectory(prefix="orion-v3-run-028-") as td:
        workspace = Path(td)
        conversation = None
        try:
            llm = LLM(
                usage_id="run-028-openhands-agent-messages",
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
                system_prompt_kwargs={"cli_mode": True},
            )
            conversation = Conversation(
                agent=agent,
                workspace=str(workspace),
                max_iteration_per_run=1,
                visualizer=None,
                delete_on_close=True,
            )

            # Public send_message() eagerly initializes a regular Agent. This creates
            # the exact SystemPromptEvent and tools_map used by the real first step.
            prompt = (
                "Use the available terminal tool exactly once. "
                "Run exactly this PowerShell command: " + COMMAND
            )
            conversation.send_message(prompt)

            terminal_tool = agent.tools_map[TerminalTool.name]
            prepared = prepare_llm_messages(
                conversation.state.view,
                condenser=agent.condenser,
                llm=llm,
            )
            if not isinstance(prepared, list):
                raise RuntimeError("unexpected condensation in first-turn calibration")

            print("NATIVE_TOOL_CALLING> " + str(llm.native_tool_calling))
            print("AGENT_TOOL_NAMES> " + ",".join(sorted(agent.tools_map.keys())))
            describe_messages("CASE_B_AGENT_PREPARED", prepared)

            control_messages = [
                Message(
                    role="user",
                    content=[TextContent(text=prompt)],
                )
            ]
            describe_messages("CASE_A_MINIMAL", control_messages)

            case_a = llm.generate(
                messages=control_messages,
                tools=[terminal_tool],
                store=False,
                add_security_risk_prediction=True,
            )
            a_ok, _ = classify("CASE_A_MINIMAL", case_a)

            case_b = llm.generate(
                messages=prepared,
                tools=[terminal_tool],
                store=False,
                add_security_risk_prediction=True,
                call_context=conversation.get_llm_call_context(),
            )
            b_ok, b_text = classify("CASE_B_AGENT_PREPARED", case_b)

            # If the exact prepared messages reproduce the textual tool form,
            # isolate the system message in the same physical run.
            if a_ok and not b_ok and len(prepared) >= 2:
                no_system = [m for m in prepared if m.role != "system"]
                describe_messages("CASE_C_NO_SYSTEM", no_system)
                case_c = llm.generate(
                    messages=no_system,
                    tools=[terminal_tool],
                    store=False,
                    add_security_risk_prediction=True,
                )
                c_ok, _ = classify("CASE_C_NO_SYSTEM", case_c)

                if c_ok:
                    print("DIAGNOSIS> AGENT_SYSTEM_MESSAGE_CHANGES_TOOL_CALL_BEHAVIOR")
                elif "<invoke" in b_text.lower():
                    print("DIAGNOSIS> AGENT_PREPARED_MESSAGES_REPRODUCE_TEXTUAL_INVOKE")
                else:
                    print("DIAGNOSIS> AGENT_PREPARED_MESSAGES_BREAK_NATIVE_TOOL_CALLING")
                print("STATUS> FAIL")
                return 1

            if a_ok and b_ok:
                print("DIAGNOSIS> AGENT_PREPARED_MESSAGES_HEALTHY")
                print("NEXT_BOUNDARY> AGENT_STEP_STREAM_OR_CALL_CONTEXT_RUNTIME")
                print("STATUS> PASS")
                return 0

            if not a_ok:
                print("DIAGNOSIS> CONTROL_REGRESSION")
            else:
                print("DIAGNOSIS> AGENT_PREPARED_MESSAGES_DIFFER")
            print("STATUS> FAIL")
            return 1
        finally:
            if conversation is not None:
                conversation.close()


if __name__ == "__main__":
    raise SystemExit(main())
