from __future__ import annotations

import json
import os
import urllib.request


MODEL = os.environ.get("ORION_CALIBRATION_MODEL", "qwen3.6:35b-a3b")
URL = "http://127.0.0.1:11434/api/chat"


def main() -> int:
    print("V3_RUN_ID> V3-RUN-025")
    print("OLLAMA_NATIVE_TOOL_CALIBRATION> START")
    print("CALIBRATION_MODEL> " + MODEL)

    payload = {
        "model": MODEL,
        "stream": False,
        "think": False,
        "options": {"temperature": 0},
        "messages": [
            {
                "role": "user",
                "content": (
                    "Call the marker tool exactly once with text "
                    "ORION_NATIVE_TOOL_CALIBRATION. Do not answer in plain text."
                ),
            }
        ],
        "tools": [
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
        ],
    }

    req = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            body = response.read().decode("utf-8")
    except Exception as exc:
        print("OLLAMA_NATIVE_REQUEST> FAIL")
        print("DETAIL> " + str(exc))
        print("STATUS> FAIL")
        return 1

    print("OLLAMA_NATIVE_REQUEST> PASS")
    print("OLLAMA_NATIVE_RAW_RESPONSE> " + body[:5000].replace("\n", " "))

    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        print("OLLAMA_NATIVE_JSON> FAIL")
        print("DETAIL> " + str(exc))
        print("STATUS> FAIL")
        return 1

    message = data.get("message") or {}
    tool_calls = message.get("tool_calls") or []
    content = str(message.get("content") or "")

    print("OLLAMA_NATIVE_TOOL_CALL_COUNT> " + str(len(tool_calls)))
    print("OLLAMA_NATIVE_TEXT_LENGTH> " + str(len(content)))

    if not tool_calls:
        print("OLLAMA_NATIVE_STRUCTURED_TOOL_CALL> FAIL")
        if content:
            print("OLLAMA_NATIVE_TEXT> " + content[-2000:].replace("\n", " "))
        print("DIAGNOSIS> MODEL_OR_OLLAMA_TEMPLATE_NO_STRUCTURED_TOOL_CALL")
        print("STATUS> FAIL")
        return 1

    first = tool_calls[0]
    function = first.get("function") or {}
    name = function.get("name")
    arguments = function.get("arguments") or {}

    print("OLLAMA_NATIVE_TOOL_NAME> " + str(name))
    print("OLLAMA_NATIVE_TOOL_ARGUMENTS> " + json.dumps(arguments, sort_keys=True))

    if name != "marker":
        print("OLLAMA_NATIVE_STRUCTURED_TOOL_CALL> FAIL")
        print("DIAGNOSIS> WRONG_TOOL_SELECTED")
        print("STATUS> FAIL")
        return 1

    if arguments.get("text") != "ORION_NATIVE_TOOL_CALIBRATION":
        print("OLLAMA_NATIVE_STRUCTURED_TOOL_CALL> FAIL")
        print("DIAGNOSIS> WRONG_TOOL_ARGUMENTS")
        print("STATUS> FAIL")
        return 1

    print("OLLAMA_NATIVE_STRUCTURED_TOOL_CALL> PASS")
    print("DIAGNOSIS> NATIVE_OLLAMA_TOOL_PATH_HEALTHY")
    print("STATUS> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
