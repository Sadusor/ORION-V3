"""Windows owner-account DPAPI Gitea token, read-only runtime injection.

No token persistence, logs or model exposure. The subprocess is local and
reads the fixed owner-owned encrypted file. Fail closed on any error.
"""
from __future__ import annotations
import os
import subprocess
import sys

_PS = """
$ErrorActionPreference='Stop'
$p=Join-Path $env:APPDATA 'ORION-V3\\gitea-readonly-token.dpapi'
if (!(Test-Path -LiteralPath $p)) { throw 'Missing encrypted token' }
$s=ConvertTo-SecureString -String ([IO.File]::ReadAllText($p).Trim())
$b=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)
try { [Console]::Out.Write([Runtime.InteropServices.Marshal]::PtrToStringBSTR($b)) }
finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b) }
"""

def read_gitea_token() -> str:
    """Prefer explicit process environment; otherwise Windows DPAPI owner token."""
    existing=os.environ.get("ORION_GITEA_TOKEN", "")
    if existing:
        return existing
    if sys.platform!="win32":
        return ""
    try:
        p=subprocess.run(
            ["powershell.exe","-NoProfile","-NonInteractive","-Command",_PS],
            stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
            text=True,timeout=8,check=False,
            creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0),
        )
    except (OSError,subprocess.TimeoutExpired):
        return ""
    return p.stdout.strip() if p.returncode==0 else ""
