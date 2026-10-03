from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

from pydantic import SecretStr

from openhands.sdk import Agent, Conversation, LLM, Message, Tool
from openhands.sdk.agent.utils import prepare_llm_messages
from openhands.sdk.llm import TextContent
from openhands.tools.preset.default import register_default_tools
from openhands.tools.terminal import TerminalTool


MODEL = os.environ.get("ORION_CALIBRATION_MODEL", "ollama_chat/qwen3.6:35b-a3b")
OLLAMA_URL = "http://127.0.0.1:11434"
COMMAND = "Write-Output ORION_SYSTEM_PROMPT_BISECT"
SECTION_RE = re.compile(r"<([A-Z][A-Z0-9_]+)>.*?</\1>", re.S)


@dataclass
class CaseResult:
    label: str
    structured: bool
    text: str


def text_of(message: Message) -> str:
    return "".join(
        item.text for item in message.content if isinstance(item, TextContent)
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def call_case(
    llm: LLM,
    tool,
    user_message: Message,
    label: str,
    *,
    system_text: str | None = None,
    call_context=None,
) -> CaseResult:
    messages: list[Message] = []
    if system_text is not None:
        messages.append(
            Message(role="system", content=[TextContent(text=system_text)])
        )
    messages.append(user_message)

    response = llm.generate(
        messages=messages,
        tools=[tool],
        store=False,
        add_security_risk_prediction=True,
        call_context=call_context,
    )

    message = response.message
    calls = list(message.tool_calls or [])
    text = text_of(message)
    structured = bool(calls) and calls[0].name == TerminalTool.name

    print(f"{label}_SYSTEM_LENGTH> {len(system_text or '')}")
    print(f"{label}_SYSTEM_SHA256> {sha256_text(system_text or '')}")
    print(f"{label}_TOOL_CALL_COUNT> {len(calls)}")
    print(f"{label}_TEXT_LENGTH> {len(text)}")
    if calls:
        call = calls[0]
        print(f"{label}_TOOL_NAME> {call.name}")
        print(
            f"{label}_TOOL_ARGUMENTS> "
            + json.dumps(
                call.arguments,
                ensure_ascii=False,
                sort_keys=True,
                default=str,
            )
        )
    if text:
        print(f"{label}_TEXT> " + text[-1600:].replace("\n", " "))
    print(
        f"{label}_STRUCTURED_TOOL_CALL> "
        + ("PASS" if structured else "FAIL")
    )
    return CaseResult(label=label, structured=structured, text=text)


def split_sections(static_text: str) -> list[tuple[str, str]]:
    matches = list(SECTION_RE.finditer(static_text))
    sections = [(match.group(1), match.group(0)) for match in matches]
    covered = sum(len(text) for _, text in sections)
    print(f"STATIC_SECTION_COUNT> {len(sections)}")
    print(f"STATIC_SECTION_MATCHED_CHARS> {covered}")
    print(f"STATIC_TOTAL_CHARS> {len(static_text)}")
    print(
        "STATIC_SECTION_NAMES> "
        + ",".join(name for name, _ in sections)
    )
    return sections


def join_sections(items: list[tuple[str, str]]) -> str:
    return "\n\n".join(text for _, text in items)


def bisect_failing_sections(
    llm: LLM,
    tool,
    user_message: Message,
    items: list[tuple[str, str]],
    *,
    depth: int = 0,
) -> tuple[str | None, str]:
    if not items:
        return None, "empty"
    if len(items) == 1:
        name, text = items[0]
        result = call_case(
            llm,
            tool,
            user_message,
            f"BISECT_D{depth}_{name}",
            system_text=text,
        )
        if result.structured:
            return None, "single_section_passed"
        return name, "single_section_failed"

    midpoint = len(items) // 2
    left = items[:midpoint]
    right = items[midpoint:]

    left_names = "+".join(name for name, _ in left)
    left_result = call_case(
        llm,
        tool,
        user_message,
        f"BISECT_D{depth}_LEFT",
        system_text=join_sections(left),
    )
    print(f"BISECT_D{depth}_LEFT_NAMES> {left_names}")
    if not left_result.structured:
        return bisect_failing_sections(
            llm, tool, user_message, left, depth=depth + 1
        )

    right_names = "+".join(name for name, _ in right)
    right_result = call_case(
        llm,
        tool,
        user_message,
        f"BISECT_D{depth}_RIGHT",
        system_text=join_sections(right),
    )
    print(f"BISECT_D{depth}_RIGHT_NAMES> {right_names}")
    if not right_result.structured:
        return bisect_failing_sections(
            llm, tool, user_message, right, depth=depth + 1
        )

    return None, "cross_group_interaction_or_length"


def main() -> int:
    print("V3_RUN_ID> V3-RUN-029")
    print("OPENHANDS_SYSTEM_PROMPT_BISECT> START")
    print("CALIBRATION_MODEL> " + MODEL)

    register_default_tools(enable_browser=False)

    with tempfile.TemporaryDirectory(prefix="orion-v3-run-029-") as td:
        workspace = Path(td)
        conversation = None
        try:
            llm = LLM(
                usage_id="run-029-openhands-system-bisect",
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

            prompt = (
                "Use the available terminal tool exactly once. "
                "Run exactly this PowerShell command: " + COMMAND
            )
            conversation.send_message(prompt)

            prepared = prepare_llm_messages(
                conversation.state.view,
                condenser=agent.condenser,
                llm=llm,
            )
            if not isinstance(prepared, list) or len(prepared) < 2:
                raise RuntimeError("unexpected first-turn Agent message shape")

            system_message = prepared[0]
            if system_message.role != "system":
                raise RuntimeError("first prepared message is not system")

            user_message = prepared[-1]
            if user_message.role != "user":
                raise RuntimeError("last prepared message is not user")

            system_blocks = [
                item.text
                for item in system_message.content
                if isinstance(item, TextContent)
            ]
            if not system_blocks:
                raise RuntimeError("Agent system message has no text blocks")

            full_system = "\n".join(system_blocks)
            call_context = conversation.get_llm_call_context()

            print("NATIVE_TOOL_CALLING> " + str(llm.native_tool_calling))
            print("AGENT_TOOL_NAMES> " + ",".join(sorted(agent.tools_map.keys())))
            print(f"SYSTEM_BLOCK_COUNT> {len(system_blocks)}")
            for index, block in enumerate(system_blocks):
                print(f"SYSTEM_BLOCK_{index}_LENGTH> {len(block)}")
                print(f"SYSTEM_BLOCK_{index}_SHA256> {sha256_text(block)}")

            control = call_case(
                llm,
                agent.tools_map[TerminalTool.name],
                user_message,
                "CONTROL_MINIMAL_NO_CONTEXT",
            )
            if not control.structured:
                print("DIAGNOSIS> CONTROL_REGRESSION")
                print("DIAGNOSTIC_STATUS> FAIL")
                print("STATUS> FAIL")
                return 1

            context_only = call_case(
                llm,
                agent.tools_map[TerminalTool.name],
                user_message,
                "CONTROL_MINIMAL_WITH_CONTEXT",
                call_context=call_context,
            )
            if not context_only.structured:
                print("DIAGNOSIS> CALL_CONTEXT_BREAKS_NATIVE_TOOL_CALLING")
                print("DIAGNOSTIC_STATUS> PASS")
                print("OPENHANDS_AGENT_SYSTEM_PATH> NOT_ISOLATED")
                print("STATUS> PASS")
                return 0

            full_without_context = call_case(
                llm,
                agent.tools_map[TerminalTool.name],
                user_message,
                "FULL_SYSTEM_NO_CONTEXT",
                system_text=full_system,
            )
            if full_without_context.structured:
                full_with_context = call_case(
                    llm,
                    agent.tools_map[TerminalTool.name],
                    user_message,
                    "FULL_SYSTEM_WITH_CONTEXT",
                    system_text=full_system,
                    call_context=call_context,
                )
                if not full_with_context.structured:
                    print(
                        "DIAGNOSIS> SYSTEM_MESSAGE_AND_CALL_CONTEXT_INTERACTION"
                    )
                else:
                    print("DIAGNOSIS> RUN028_NONDETERMINISTIC_NOT_REPRODUCED")
                print("DIAGNOSTIC_STATUS> PASS")
                print("OPENHANDS_AGENT_SYSTEM_PATH> UNRESOLVED")
                print("STATUS> PASS")
                return 0

            print("SYSTEM_MESSAGE_SUFFICIENT> PASS")

            block_results: list[tuple[int, CaseResult]] = []
            for index, block in enumerate(system_blocks):
                result = call_case(
                    llm,
                    agent.tools_map[TerminalTool.name],
                    user_message,
                    f"SYSTEM_BLOCK_{index}_ONLY",
                    system_text=block,
                )
                block_results.append((index, result))

            failing_blocks = [
                index for index, result in block_results if not result.structured
            ]
            print(
                "FAILING_SYSTEM_BLOCKS> "
                + ",".join(str(index) for index in failing_blocks)
            )

            if len(failing_blocks) != 1:
                print(
                    "DIAGNOSIS> SYSTEM_BLOCK_INTERACTION_OR_MULTIPLE_BAD_BLOCKS"
                )
                print("DIAGNOSTIC_STATUS> PASS")
                print("OPENHANDS_AGENT_SYSTEM_PATH> FAIL")
                print("STATUS> PASS")
                return 0

            failing_index = failing_blocks[0]
            failing_text = system_blocks[failing_index]
            sections = split_sections(failing_text)
            if len(sections) < 2:
                print("DIAGNOSIS> SINGLE_FAILING_SYSTEM_BLOCK_NOT_SECTIONABLE")
                print("DIAGNOSTIC_STATUS> PASS")
                print("OPENHANDS_AGENT_SYSTEM_PATH> FAIL")
                print("STATUS> PASS")
                return 0

            culprit, mode = bisect_failing_sections(
                llm,
                agent.tools_map[TerminalTool.name],
                user_message,
                sections,
            )
            print("BISECT_MODE> " + mode)

            if culprit is None:
                print(
                    "DIAGNOSIS> STATIC_PROMPT_INTERACTION_OR_LENGTH_EFFECT"
                )
                print("DIAGNOSTIC_STATUS> PASS")
                print("OPENHANDS_AGENT_SYSTEM_PATH> FAIL")
                print("STATUS> PASS")
                return 0

            print("CULPRIT_SECTION_CANDIDATE> " + culprit)

            without_culprit = [
                item for item in sections if item[0] != culprit
            ]
            removal = call_case(
                llm,
                agent.tools_map[TerminalTool.name],
                user_message,
                "STATIC_WITHOUT_CULPRIT",
                system_text=join_sections(without_culprit),
            )
            if removal.structured:
                print(
                    "DIAGNOSIS> SINGLE_STATIC_SECTION_NECESSARY_AND_SUFFICIENT"
                )
            else:
                print(
                    "DIAGNOSIS> CULPRIT_SECTION_SUFFICIENT_BUT_NOT_UNIQUE"
                )

            print("DIAGNOSTIC_STATUS> PASS")
            print("OPENHANDS_AGENT_SYSTEM_PATH> FAIL")
            print("STATUS> PASS")
            return 0
        finally:
            if conversation is not None:
                conversation.close()


if __name__ == "__main__":
    raise SystemExit(main())
