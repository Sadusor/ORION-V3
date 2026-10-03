from __future__ import annotations

import json
import os
import sys

import litellm


MODEL = os.environ.get("ORION_CALIBRATION_MODEL", "ollama_chat/qwen3.6:35b-a3b")
API_BASE = "http://127.0.0.1:11434"


def main() -> int:
    print("V3_RUN_ID> V3-RUN-026")
    print("LITELLM_DIRECT_TOOL_CALIBRATION> START")
    print("CALIBRATION_MODEL> " + MODEL)
    print("LITELLM_VERSION> " + str(getattr(litellm, "__version__", "unknown")))

    tools = [
        {
            "type": "function",
            "function": {
                "name": "marker",
                "description": "Record one exact diagnostic marker.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Exact marker text.",
                        }
                    },
                    "required": ["text"],
                },
            },
        }
    ]

    try:
        response = litellm.completion(
            model=MODEL,
            api_base=API_BASE,
            api_key="ollama",
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Call the marker tool exactly once with text "
                        "ORION_LITELLM_TOOL_CALIBRATION. Do not answer in plain text."
                    ),
                }
            ],
            tools=tools,
            temperature=0,
            stream=False,
        )
    except Exception as exc:
        print("LITELLM_DIRECT_REQUEST> FAIL")
        print("DETAIL_TYPE> " + type(exc).__name__)
        print("DETAIL> " + str(exc)[-3000:])
        print("STATUS> FAIL")
        return 1

    print("LITELLM_DIRECT_REQUEST> PASS")

    if hasattr(response, "model_dump"):
        dumped = response.model_dump()
    elif isinstance(response, dict):
        dumped = response
    else:
        dumped = {"repr": repr(response)}

    raw = json.dumps(dumped, ensure_ascii=False, default=str)
    print("LITELLM_DIRECT_RAW_RESPONSE> " + raw[:7000].replace("\n", " "))

    choices = getattr(response, "choices", None) or []
    if not choices:
        print("LITELLM_DIRECT_CHOICES> FAIL")
        print("STATUS> FAIL")
        return 1

    message = getattr(choices[0], "message", None)
    if message is None:
        print("LITELLM_DIRECT_MESSAGE> FAIL")
        print("STATUS> FAIL")
        return 1

    content = getattr(message, "content", None) or ""
    tool_calls = getattr(message, "tool_calls", None) or []

    print("LITELLM_DIRECT_TOOL_CALL_COUNT> " + str(len(tool_calls)))
    print("LITELLM_DIRECT_TEXT_LENGTH> " + str(len(content)))

    if not tool_calls:
        print("LITELLM_DIRECT_STRUCTURED_TOOL_CALL> FAIL")
        if content:
            print("LITELLM_DIRECT_TEXT> " + str(content)[-2500:].replace("\n", " "))
        print("DIAGNOSIS> LITELLM_OLLAMA_CHAT_LOSES_STRUCTURED_TOOL_CALL")
        print("STATUS> FAIL")
        return 1

    first = tool_calls[0]
    function = getattr(first, "function", None)
    if function is None and isinstance(first, dict):
        function = first.get("function")

    if isinstance(function, dict):
        name = function.get("name")
        arguments = function.get("arguments")
    else:
        name = getattr(function, "name", None)
        arguments = getattr(function, "arguments", None)

    if isinstance(arguments, str):
        try:
            parsed_arguments = json.loads(arguments)
        except json.JSONDecodeError:
            parsed_arguments = {"_raw": arguments}
    elif isinstance(arguments, dict):
        parsed_arguments = arguments
    else:
        parsed_arguments = {}

    print("LITELLM_DIRECT_TOOL_NAME> " + str(name))
    print(
        "LITELLM_DIRECT_TOOL_ARGUMENTS> "
        + json.dumps(parsed_arguments, ensure_ascii=False, sort_keys=True)
    )

    if name != "marker":
        print("LITELLM_DIRECT_STRUCTURED_TOOL_CALL> FAIL")
        print("DIAGNOSIS> LITELLM_WRONG_TOOL")
        print("STATUS> FAIL")
        return 1

    if parsed_arguments.get("text") != "ORION_LITELLM_TOOL_CALIBRATION":
        print("LITELLM_DIRECT_STRUCTURED_TOOL_CALL> FAIL")
        print("DIAGNOSIS> LITELLM_WRONG_TOOL_ARGUMENTS")
        print("STATUS> FAIL")
        return 1

    print("LITELLM_DIRECT_STRUCTURED_TOOL_CALL> PASS")
    print("DIAGNOSIS> LITELLM_DIRECT_TOOL_PATH_HEALTHY")
    print("STATUS> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
