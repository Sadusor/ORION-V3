"""V2 source reader for approved local Gitea content; reference data only."""
from __future__ import annotations

from .gitea_readonly_v1 import GiteaReadonly
from .gitea_source_context_v1 import get_source_context

def get_source_context_v2(api: GiteaReadonly, owner: str, repo: str,
                          commit: str, path: str) -> dict:
    """Allow approved 64-KiB text while preserving V1's path and content checks."""
    # Keep V1 as the authority for small files.
    try:
        return get_source_context(api, owner, repo, commit, path)
    except ValueError as exc:
        if str(exc) not in {"Unsupported or oversized file", "File too large"}:
            raise
    from .gitea_readonly_v1 import _segment
    import base64
    import re
    if not re.fullmatch(r"[0-9a-fA-F]{40}", commit):
        raise ValueError("Exact commit required")
    parts = path.split("/")
    if not 1 <= len(parts) <= 32 or len(path) > 400:
        raise ValueError("Invalid path")
    if any(not p or p in (".", "..") for p in parts):
        raise ValueError("Invalid path")
    if any(p.lower() in (".git", "node_modules", ".venv") for p in parts):
        raise ValueError("Excluded directory")
    if parts[-1].lower() in {".env", "app.ini", "credentials.json", "secrets.json", "id_rsa"}:
        raise ValueError("Sensitive file")
    if parts[-1].lower().endswith((".pem", ".key")):
        raise ValueError("Sensitive file")
    endpoint = "repos/{}/{}/contents/{}?ref={}".format(
        _segment(owner), _segment(repo), "/".join(_segment(p) for p in parts), commit
    )
    payload = api._get(endpoint)
    if not isinstance(payload, dict) or payload.get("type") != "file":
        raise ValueError("Invalid source")
    if payload.get("encoding") != "base64" or payload.get("size", 65537) > 65536:
        raise ValueError("V2 source limit")
    raw = base64.b64decode(payload["content"], validate=True)
    if len(raw) > 65536 or bytes([0]) in raw:
        raise ValueError("Oversized or binary source")
    return {"repository":owner+"/"+repo, "commit":commit, "path":path,
            "text":raw.decode("utf-8"), "trust":"untrusted_source", "read_only":True}
