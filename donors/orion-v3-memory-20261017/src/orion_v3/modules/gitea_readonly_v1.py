"""Read-only local Gitea repository inspection. No execution or write authority.

The caller must authenticate the ORION owner, enforce project authorization,
redact secrets, and treat returned repository content as untrusted data.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

MAX_RESPONSE_BYTES = 2_000_000
ALLOWED_BASE_HOSTS = {"127.0.0.1", "localhost", "::1"}


def _segment(value: str) -> str:
    if not isinstance(value, str) or not value or value in {".", ".."}:
        raise ValueError("A nonempty safe path segment is required")
    if any(c in value for c in ("\\", "/", "\x00", "?", "#")):
        raise ValueError("Unsafe Git resource segment")
    return quote(value, safe="")


@dataclass(frozen=True)
class GiteaReadonly:
    base_url: str
    token: str = ""
    timeout_seconds: float = 8.0

    def __post_init__(self):
        parsed = urlsplit(self.base_url)
        if parsed.scheme != "http" or parsed.hostname not in ALLOWED_BASE_HOSTS:
            raise ValueError("Gitea V1 permits loopback HTTP only")
        if parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path.strip("/"):
            raise ValueError("Base URL must be the loopback origin only")
        if not parsed.port or parsed.port < 1:
            raise ValueError("An explicit local Gitea port is required")
        if not (0 < self.timeout_seconds <= 30):
            raise ValueError("Invalid timeout")

    def _get(self, path: str):
        headers = {"Accept": "application/json", "User-Agent": "ORION-V3-Gitea-ReadOnly/1"}
        if self.token:
            headers["Authorization"] = "token " + self.token
        req = Request(self.base_url.rstrip("/") + "/api/v1/" + path, headers=headers, method="GET")
        # Do not follow redirects: a local Gitea server must never bounce our token elsewhere.
        from urllib.request import build_opener, HTTPRedirectHandler
        class NoRedirect(HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None
        with build_opener(NoRedirect()).open(req, timeout=self.timeout_seconds) as response:
            if response.status != 200:
                raise RuntimeError("Gitea returned non-200")
            data = response.read(MAX_RESPONSE_BYTES + 1)
            if len(data) > MAX_RESPONSE_BYTES:
                raise ValueError("Gitea response exceeds limit")
        return json.loads(data.decode("utf-8"))

    def list_repositories(self, page: int = 1, limit: int = 50):
        if not 1 <= page <= 10000 or not 1 <= limit <= 100:
            raise ValueError("Invalid pagination")
        result = self._get(f"user/repos?page={page}&limit={limit}")
        if not isinstance(result, list):
            raise ValueError("Invalid Gitea repositories response")
        return [{"owner": item["owner"]["login"], "name": item["name"],
                 "default_branch": item.get("default_branch", ""),
                 "private": bool(item.get("private", False))}
                for item in result]

    def repository(self, owner: str, name: str):
        item = self._get(f"repos/{_segment(owner)}/{_segment(name)}")
        return {"owner": item["owner"]["login"], "name": item["name"],
                "default_branch": item.get("default_branch", ""),
                "private": bool(item.get("private", False))}

    def branches(self, owner: str, name: str, page: int = 1, limit: int = 50):
        if not 1 <= page <= 10000 or not 1 <= limit <= 100:
            raise ValueError("Invalid pagination")
        result = self._get(f"repos/{_segment(owner)}/{_segment(name)}/branches?page={page}&limit={limit}")
        if not isinstance(result, list):
            raise ValueError("Invalid branches response")
        return [{"name": item["name"], "commit_id": item["commit"]["id"]} for item in result]

    def tree(self, owner: str, name: str, commit_sha: str):
        if len(commit_sha) != 40 or any(c not in "0123456789abcdefABCDEF" for c in commit_sha):
            raise ValueError("Exact 40-character commit SHA required")
        result = self._get(f"repos/{_segment(owner)}/{_segment(name)}/git/trees/{commit_sha}?recursive=true")
        if not isinstance(result, dict) or not isinstance(result.get("tree"), list):
            raise ValueError("Invalid tree response")
        return {"sha": result.get("sha", ""), "truncated": bool(result.get("truncated", False)),
                "tree": [{"path": x["path"], "type": x["type"], "sha": x.get("sha", "")}
                         for x in result["tree"][:5000]]}
