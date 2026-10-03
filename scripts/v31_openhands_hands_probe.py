from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SDK = ROOT / "external" / "OpenHands-software-agent-sdk"

if not SDK.exists():
    raise SystemExit("Pinned OpenHands SDK donor is missing.")

# uv workspace makes the donor packages importable when this script is executed
# with --project <SDK> --package openhands-tools.
sys.path.insert(0, str(ROOT / "src"))

from openhands.tools.file_editor.definition import FileEditorAction
from openhands.tools.file_editor.impl import FileEditorExecutor
from openhands.tools.terminal.definition import TerminalAction
from openhands.tools.terminal.impl import TerminalExecutor


def pid_exists_windows(pid: int) -> bool:
    proc = subprocess.run(
        ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
        check=False,
    )
    text = (proc.stdout or "").strip()
    if not text or text.startswith("INFO:"):
        return False
    return f'"{pid}"' in text or f",{pid}," in text or str(pid) in text


print("V3_RUN_ID> V3-RUN-008")
print("OPENHANDS_HANDS_ONLY> START")
print("OPENHANDS_AGENT_LOOP> NONE")

workspace = ROOT / ".vendor" / "v3-run-008-openhands-hands"
workspace.mkdir(parents=True, exist_ok=True)

allowed = workspace / "allowed.py"
blocked = workspace / "blocked.py"
pid_file = workspace / "child.pid"
spawn_script = workspace / "wait_on_child.ps1"

allowed.write_text(
    "VALUE = 1\n\ndef answer():\n    return VALUE\n",
    encoding="utf-8",
)
blocked.write_text("BLOCKED = True\n", encoding="utf-8")
pid_file.unlink(missing_ok=True)

# ---------------------------------------------------------------------------
# A. OpenHands FileEditor used as a Hand only, with explicit edit allowlist.
# ---------------------------------------------------------------------------
editor = FileEditorExecutor(
    workspace_root=str(workspace),
    allowed_edits_files=[str(allowed)],
)

before = allowed.read_text(encoding="utf-8")
edit = editor(
    FileEditorAction(
        command="str_replace",
        path=str(allowed.resolve()),
        old_str="VALUE = 1",
        new_str="VALUE = 2",
    )
)
assert not edit.is_error, edit
assert allowed.read_text(encoding="utf-8").startswith("VALUE = 2")
assert edit.old_content == before
assert edit.new_content is not None and edit.new_content.startswith("VALUE = 2")

blocked_before = blocked.read_text(encoding="utf-8")
denied = editor(
    FileEditorAction(
        command="str_replace",
        path=str(blocked.resolve()),
        old_str="BLOCKED = True",
        new_str="BLOCKED = False",
    )
)
assert denied.is_error is True, denied
assert blocked.read_text(encoding="utf-8") == blocked_before

undo = editor(
    FileEditorAction(
        command="undo_edit",
        path=str(allowed.resolve()),
    )
)
assert not undo.is_error, undo
assert allowed.read_text(encoding="utf-8") == before

print("OPENHANDS_FILE_EDITOR_ALLOWED_EDIT> PASS")
print("OPENHANDS_FILE_EDITOR_OUT_OF_SCOPE_EDIT> DENIED")
print("OPENHANDS_FILE_EDITOR_BEFORE_AFTER_EVIDENCE> PASS")
print("OPENHANDS_FILE_EDITOR_UNDO> PASS")

# Explicitly record the source-audit result: workspace_root itself is not a
# security boundary, so ORION may reuse editor mechanics only with an ORION
# trusted binding / exact allowlist.
print("OPENHANDS_WORKSPACE_ROOT_SECURITY_BOUNDARY> NO")
print("OPENHANDS_ALLOWED_EDITS_FILES> REQUIRED_FOR_ORION_ADAPTER")

# ---------------------------------------------------------------------------
# B. OpenHands Windows terminal used as a Hand only.
# ---------------------------------------------------------------------------
terminal = TerminalExecutor(
    working_dir=str(workspace),
    terminal_type="powershell",
    no_change_timeout_seconds=1,
)

try:
    smoke = terminal(
        TerminalAction(
            command="Write-Output 'ORION_TERMINAL_OK'",
            timeout=10,
        )
    )
    assert smoke.metadata.exit_code == 0, smoke
    assert "ORION_TERMINAL_OK" in smoke.text, smoke.text
    print("OPENHANDS_WINDOWS_TERMINAL_EXEC> PASS")

    spawn_script.write_text(
        "\n".join(
            [
                f"$pidPath = '{str(pid_file).replace(chr(39), chr(39) * 2)}'",
                "$child = Start-Process -FilePath powershell.exe "
                "-ArgumentList '-NoLogo','-NoProfile','-Command',"
                "'Start-Sleep -Seconds 120' -PassThru",
                "Set-Content -LiteralPath $pidPath -Value $child.Id",
                "Wait-Process -Id $child.Id",
            ]
        ),
        encoding="utf-8",
    )

    long_run = terminal(
        TerminalAction(
            command=f"& '{str(spawn_script).replace(chr(39), chr(39) * 2)}'",
        )
    )
    assert long_run.metadata.exit_code == -1, long_run

    deadline = time.time() + 5
    while not pid_file.exists() and time.time() < deadline:
        time.sleep(0.1)
    assert pid_file.exists(), "child PID evidence file not created"

    child_pid = int(pid_file.read_text(encoding="utf-8").strip())
    assert pid_exists_windows(child_pid), f"child PID {child_pid} never became visible"

    terminal(
        TerminalAction(
            command="C-c",
            is_input=True,
            timeout=3,
        )
    )

    deadline = time.time() + 6
    while pid_exists_windows(child_pid) and time.time() < deadline:
        time.sleep(0.1)

    assert not pid_exists_windows(child_pid), (
        f"OpenHands terminal interrupt left child PID {child_pid} alive"
    )

    print("OPENHANDS_WINDOWS_TERMINAL_INTERRUPT> PASS")
    print("OPENHANDS_WINDOWS_CHILD_PROCESS_GONE> PASS")
    print("OPENHANDS_TERMINAL_STOP_CANDIDATE> PASS")
finally:
    terminal.close()
    # Defensive cleanup if a donor regression leaves the synthetic child alive.
    if pid_file.exists():
        try:
            child_pid = int(pid_file.read_text(encoding="utf-8").strip())
        except Exception:
            child_pid = 0
        if child_pid and pid_exists_windows(child_pid):
            subprocess.run(
                ["taskkill", "/PID", str(child_pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )

print("OPENHANDS_HANDS_ONLY> PASS")
print("STATUS> PASS")
