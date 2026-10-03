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
COMMAND = "Write-Output ORION_PROMPT_INTERACTION"
SECTION_RE = re.compile(r"<([A-Z][A-Z0-9_]+)>.*?</\1>", re.S)


@dataclass
class Result:
    label: str
    structured: bool
    text: str
    length: int


def text_of(message: Message) -> str:
    return "".join(
        item.text for item in message.content if isinstance(item, TextContent)
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def join_sections(items: list[tuple[str, str]]) -> str:
    return "\n\n".join(text for _, text in items)


def neutral_text(length: int) -> str:
    unit = "Reference context only. "
    if length <= 0:
        return ""
    repeated = (unit * ((length // len(unit)) + 1))[:length]
    assert len(repeated) == length
    return repeated


def run_case(
    llm: LLM,
    tool,
    user_message: Message,
    label: str,
    system_text: str | None,
) -> Result:
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
    )
    message = response.message
    calls = list(message.tool_calls or [])
    text = text_of(message)
    structured = bool(calls) and calls[0].name == TerminalTool.name
    length = len(system_text or "")

    print(f"{label}_SYSTEM_LENGTH> {length}")
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
        print(f"{label}_TEXT> " + text[-1400:].replace("\n", " "))
    print(
        f"{label}_STRUCTURED_TOOL_CALL> "
        + ("PASS" if structured else "FAIL")
    )
    return Result(label=label, structured=structured, text=text, length=length)


def main() -> int:
    print("V3_RUN_ID> V3-RUN-030")
    print("OPENHANDS_PROMPT_LENGTH_INTERACTION> START")
    print("CALIBRATION_MODEL> " + MODEL)

    register_default_tools(enable_browser=False)

    with tempfile.TemporaryDirectory(prefix="orion-v3-run-030-") as td:
        conversation = None
        try:
            llm = LLM(
                usage_id="run-030-openhands-prompt-interaction",
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
                workspace=str(Path(td)),
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
            user_message = prepared[-1]
            if system_message.role != "system" or user_message.role != "user":
                raise RuntimeError("unexpected prepared message roles")

            blocks = [
                item.text
                for item in system_message.content
                if isinstance(item, TextContent)
            ]
            if len(blocks) != 1:
                raise RuntimeError(
                    "RUN-030 expects exactly one rendered system text block"
                )
            full_system = blocks[0]

            matches = list(SECTION_RE.finditer(full_system))
            sections = [(m.group(1), m.group(0)) for m in matches]
            if len(sections) != 16:
                raise RuntimeError(
                    f"expected 16 rendered static sections, got {len(sections)}"
                )

            reconstructed = join_sections(sections)
            if reconstructed != full_system:
                raise RuntimeError(
                    "rendered section reconstruction does not equal full system prompt"
                )

            tool = agent.tools_map[TerminalTool.name]
            print("NATIVE_TOOL_CALLING> " + str(llm.native_tool_calling))
            print("FULL_SYSTEM_LENGTH> " + str(len(full_system)))
            print("FULL_SYSTEM_SHA256> " + sha256_text(full_system))
            print(
                "SECTION_NAMES> "
                + ",".join(name for name, _ in sections)
            )

            control = run_case(
                llm, tool, user_message, "CONTROL_MINIMAL", None
            )
            if not control.structured:
                print("DIAGNOSIS> CONTROL_REGRESSION")
                print("DIAGNOSTIC_STATUS> FAIL")
                print("STATUS> FAIL")
                return 1

            original = run_case(
                llm, tool, user_message, "FULL_ORIGINAL", full_system
            )
            if original.structured:
                repeat = run_case(
                    llm,
                    tool,
                    user_message,
                    "FULL_ORIGINAL_REPEAT",
                    full_system,
                )
                if repeat.structured:
                    print("DIAGNOSIS> RUN029_FAILURE_NOT_REPRODUCED")
                    print("DIAGNOSTIC_STATUS> PASS")
                    print("OPENHANDS_AGENT_SYSTEM_PATH> NONDETERMINISTIC")
                    print("STATUS> PASS")
                    return 0

            midpoint = len(sections) // 2
            left = sections[:midpoint]
            right = sections[midpoint:]

            swapped = run_case(
                llm,
                tool,
                user_message,
                "FULL_HALVES_SWAPPED",
                join_sections(right + left),
            )
            reversed_result = run_case(
                llm,
                tool,
                user_message,
                "FULL_SECTIONS_REVERSED",
                join_sections(list(reversed(sections))),
            )
            neutral = run_case(
                llm,
                tool,
                user_message,
                "FULL_NEUTRAL_SAME_CHARS",
                neutral_text(len(full_system)),
            )

            first_failing_prefix: int | None = None
            previous_passing_prefix: int | None = None
            prefix_results: dict[int, Result] = {}

            for count in range(8, len(sections) + 1):
                label = f"PREFIX_{count}"
                result = run_case(
                    llm,
                    tool,
                    user_message,
                    label,
                    join_sections(sections[:count]),
                )
                prefix_results[count] = result
                if result.structured:
                    previous_passing_prefix = count
                    continue
                first_failing_prefix = count
                break

            print(
                "FIRST_FAILING_PREFIX_COUNT> "
                + (
                    str(first_failing_prefix)
                    if first_failing_prefix is not None
                    else "NONE"
                )
            )
            print(
                "PREVIOUS_PASSING_PREFIX_COUNT> "
                + (
                    str(previous_passing_prefix)
                    if previous_passing_prefix is not None
                    else "NONE"
                )
            )

            replacement_structured: bool | None = None
            added_section_structured: bool | None = None
            if (
                first_failing_prefix is not None
                and first_failing_prefix > 1
            ):
                index = first_failing_prefix - 1
                name, section_text = sections[index]
                print("BOUNDARY_ADDED_SECTION> " + name)
                print(
                    "BOUNDARY_ADDED_SECTION_LENGTH> "
                    + str(len(section_text))
                )

                section_alone = run_case(
                    llm,
                    tool,
                    user_message,
                    "BOUNDARY_SECTION_ALONE",
                    section_text,
                )
                added_section_structured = section_alone.structured

                base = join_sections(sections[:index])
                separator = "\n\n" if base else ""
                replacement_text = (
                    base
                    + separator
                    + neutral_text(len(section_text))
                )
                replacement = run_case(
                    llm,
                    tool,
                    user_message,
                    "BOUNDARY_NEUTRAL_REPLACEMENT",
                    replacement_text,
                )
                replacement_structured = replacement.structured

            if not original.structured:
                if (
                    neutral.structured
                    and swapped.structured
                    and reversed_result.structured
                ):
                    diagnosis = "ORIGINAL_SECTION_ORDER_INTERACTION"
                elif neutral.structured and (
                    swapped.structured or reversed_result.structured
                ):
                    diagnosis = "SEMANTIC_ORDER_INTERACTION_DOMINANT"
                elif not neutral.structured:
                    diagnosis = "PROMPT_LENGTH_OR_DENSITY_DOMINANT"
                elif (
                    replacement_structured is True
                    and added_section_structured is True
                ):
                    diagnosis = "CUMULATIVE_SECTION_INTERACTION_AT_BOUNDARY"
                else:
                    diagnosis = "MIXED_LENGTH_AND_SEMANTIC_INTERACTION"
            else:
                diagnosis = "FULL_PROMPT_NONDETERMINISM"

            print("DIAGNOSIS> " + diagnosis)
            print(
                "FULL_HALVES_SWAPPED_HEALTHY> "
                + ("YES" if swapped.structured else "NO")
            )
            print(
                "FULL_SECTIONS_REVERSED_HEALTHY> "
                + ("YES" if reversed_result.structured else "NO")
            )
            print(
                "FULL_NEUTRAL_SAME_CHARS_HEALTHY> "
                + ("YES" if neutral.structured else "NO")
            )
            if replacement_structured is not None:
                print(
                    "BOUNDARY_NEUTRAL_REPLACEMENT_HEALTHY> "
                    + ("YES" if replacement_structured else "NO")
                )
            if added_section_structured is not None:
                print(
                    "BOUNDARY_SECTION_ALONE_HEALTHY> "
                    + ("YES" if added_section_structured else "NO")
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
