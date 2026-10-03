from __future__ import annotations

import json
import sys
from pathlib import Path

from openhands.tools.file_editor.definition import FileEditorAction
from openhands.tools.file_editor.impl import FileEditorExecutor


RESULT_START = "---ORION_OPENHANDS_RESULT_START---"
RESULT_END = "---ORION_OPENHANDS_RESULT_END---"


def emit(payload: dict) -> None:
    print(RESULT_START)
    print(json.dumps(payload, ensure_ascii=False))
    print(RESULT_END)


def main() -> int:
    raw = sys.stdin.read()
    try:
        request = json.loads(raw)
    except json.JSONDecodeError:
        emit({"success": False, "error": "invalid_json"})
        return 2

    if not isinstance(request, dict) or request.get("operation") != "str_replace":
        emit({"success": False, "error": "unsupported_operation"})
        return 2

    target_raw = request.get("target_path")
    old_str = request.get("old_str")
    new_str = request.get("new_str")
    if not isinstance(target_raw, str) or not target_raw:
        emit({"success": False, "error": "invalid_target"})
        return 2
    if not isinstance(old_str, str) or not old_str:
        emit({"success": False, "error": "invalid_old_str"})
        return 2
    if not isinstance(new_str, str):
        emit({"success": False, "error": "invalid_new_str"})
        return 2

    target = Path(target_raw).resolve()
    editor = FileEditorExecutor(
        workspace_root=str(target.parent),
        allowed_edits_files=[str(target)],
    )
    observation = editor(
        FileEditorAction(
            command="str_replace",
            path=str(target),
            old_str=old_str,
            new_str=new_str,
        )
    )

    emit(
        {
            "success": not observation.is_error,
            "command": observation.command,
            "changed": (
                observation.old_content is not None
                and observation.new_content is not None
                and observation.old_content != observation.new_content
            ),
        }
    )
    return 0 if not observation.is_error else 1


if __name__ == "__main__":
    raise SystemExit(main())
