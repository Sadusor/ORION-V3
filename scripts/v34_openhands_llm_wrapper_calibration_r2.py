from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from pydantic import SecretStr

from openhands.sdk import Agent, Conversation, LLM, Message, Tool
from openhands.sdk.llm import TextContent
from openhands.tools.preset.default import register_default_tools
from openhands.tools.terminal import TerminalTool


MODEL = os.environ.get("ORION_CALIBRATION_MODEL", "ollama_chat/qwen3.6:35b-a3b")
OLLAMA_URL = "http://127.0.0.1:11434"


def extract(response):
    message = response.message
    calls = list(message.tool_calls or [])
    text = "".join(
        part.text for part in message.content if isinstance(part, TextContent)
    )
    return calls, text


def run_case(llm: LLM, terminal_tool, *, security: bool) -> bool:
    marker = "SECURITY_ON" if security else "SECURITY_OFF"
    response = llm.generate(
        messages=[
            Message(
                role="user",
                content=[
                    TextContent(
                        text=(
                            "Use the available terminal tool exactly once. "
                            "Run exactly this PowerShell command: "
                            "Write-Output ORION_OPENHANDS_LLM_" + marker
                        )
                    )
                ],
            )
        ],
        tools=[terminal_tool],
        store=False,
        add_security_risk_prediction=security,
    )

    calls, text = extract(response)
    print(f"{marker}_TOOL_CALL_COUNT> {len(calls)}")
    print(f"{marker}_TEXT_LENGTH> {len(text)}")
    if text:
        print(f"{marker}_TEXT> " + text[-2000:].replace("\n", " "))

    if not calls:
        print(f"{marker}_STRUCTURED_TOOL_CALL> FAIL")
        return False

    call = calls[0]
    print(f"{marker}_TOOL_NAME> {call.name}")
    print(
        f"{marker}_TOOL_ARGUMENTS> "
        + json.dumps(call.arguments, ensure_ascii=False, sort_keys=True, default=str)
    )
    ok = call.name == TerminalTool.name
    print(f"{marker}_STRUCTURED_TOOL_CALL> " + ("PASS" if ok else "FAIL"))
    return ok


def main() -> int:
    print("V3_RUN_ID> V3-RUN-027")
    print("OPENHANDS_LLM_WRAPPER_CALIBRATION> START")
    print("CALIBRATION_MODEL> " + MODEL)

    register_default_tools(enable_browser=False)

    with tempfile.TemporaryDirectory(prefix="orion-v3-run-027-") as td:
        workspace = Path(td)

        llm = LLM(
            usage_id="run-027-openhands-llm",
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

        terminal_tool = TerminalTool.create(conversation.state)[0]

        schema_off = terminal_tool.to_openai_tool(
            add_security_risk_prediction=False
        )
        schema_on = terminal_tool.to_openai_tool(
            add_security_risk_prediction=True
        )
        print(
            "TERMINAL_SCHEMA_SECURITY_OFF> "
            + json.dumps(schema_off, ensure_ascii=False, sort_keys=True)[:5000]
        )
        print(
            "TERMINAL_SCHEMA_SECURITY_ON> "
            + json.dumps(schema_on, ensure_ascii=False, sort_keys=True)[:5000]
        )

        off_ok = run_case(llm, terminal_tool, security=False)
        on_ok = run_case(llm, terminal_tool, security=True)

        conversation.close()

    if off_ok and on_ok:
        print("DIAGNOSIS> OPENHANDS_LLM_WRAPPER_AND_SECURITY_SCHEMA_HEALTHY")
        print("STATUS> PASS")
        return 0

    if off_ok and not on_ok:
        print("DIAGNOSIS> OPENHANDS_SECURITY_SCHEMA_BREAKS_TOOL_CALLING")
    elif not off_ok and on_ok:
        print("DIAGNOSIS> UNEXPECTED_SECURITY_SCHEMA_ONLY_PASS")
    else:
        print("DIAGNOSIS> OPENHANDS_LLM_WRAPPER_OR_TERMINAL_SCHEMA_BREAKS_TOOL_CALLING")

    print("STATUS> FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
