"""Read-only Windows isolation host capability inventory.

Reports prerequisites, never authorizes or launches generated code.
"""
import os
import platform
import shutil
import subprocess

def inspect_host(*, runner=subprocess.run):
    if os.name != "nt":
        return {"host": platform.system(), "qualified": False,
                "reason": "WINDOWS_REQUIRED"}
    checks = {}
    for name, command in {
        "powershell": ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", "$PSVersionTable.PSVersion.Major"],
        "whoami": ["whoami.exe", "/user"],
    }.items():
        if shutil.which(command[0]) is None:
            checks[name] = "MISSING"
            continue
        try:
            result = runner(command, capture_output=True, text=True, timeout=8,
                            check=False)
            checks[name] = "AVAILABLE" if result.returncode == 0 else "FAILED"
        except (OSError, subprocess.TimeoutExpired):
            checks[name] = "FAILED"
    return {"host": "Windows", "checks": checks, "qualified": False,
            "reason": "HOST_CAPABILITY_ONLY_NO_BOUNDARY_PROOF"}
