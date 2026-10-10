"""Read-only source context from a pinned Gitea commit."""
from __future__ import annotations
import base64
import re
from .gitea_readonly_v1 import GiteaReadonly, _segment

SHA40 = re.compile(r"^[a-fA-F0-9]{40}$")
MAX_BYTES = 32768

def get_source_context(api: GiteaReadonly, owner: str, repo: str, commit: str, path: str) -> dict:
    if not SHA40.fullmatch(commit):
        raise ValueError("A pinned commit is required")
    parts = path.split("/")
    if not 1 <= len(parts) <= 32 or len(path) > 400:
        raise ValueError("Invalid path")
    if any(not part or part in (".", "..") for part in parts):
        raise ValueError("Invalid path segments")
    blocked = {".env", "app.ini", "credentials.json", "secrets.json", "id_rsa"}
    if parts[-1].lower() in blocked or parts[-1].lower().endswith((".pem", ".key")):
        raise ValueError("Sensitive file excluded")
    if any(part.lower() in (".git", "node_modules", ".venv") for part in parts):
        raise ValueError("Excluded directory")
    uri = "repos/{}/{}/contents/{}?ref={}".format(
        _segment(owner), _segment(repo), "/".join(_segment(p) for p in parts), commit)
    payload = api._get(uri)
    if not isinstance(payload, dict) or payload.get("type") != "file":
        raise ValueError("File not found")
    if payload.get("encoding") != "base64" or payload.get("size", MAX_BYTES+1) > MAX_BYTES:
        raise ValueError("Unsupported or oversized file")
    raw = base64.b64decode(payload["content"], validate=False)
    if len(raw) > MAX_BYTES:
        raise ValueError("File too large")
    content = raw.decode("utf-8")
    if "\x00" in content:
        raise ValueError("Binary file")
    return {"repository": owner+"/"+repo, "commit": commit, "path": path,
            "text": content, "trust": "untrusted_source", "read_only": True}
