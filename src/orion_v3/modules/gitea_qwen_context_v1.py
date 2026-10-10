"""Bounded project-scoped repository context for Qwen; no model or write authority."""
from __future__ import annotations
from .gitea_readonly_v1 import GiteaReadonly
from .gitea_codebase_map_v1 import create_codebase_map
from .gitea_source_context_v1 import get_source_context

def build_repository_context(api: GiteaReadonly, *, owner: str, repo: str,
                             allowed_repository: str, paths: list[str],
                             max_total_chars: int = 16000) -> dict:
    if owner + "/" + repo != allowed_repository:
        raise PermissionError("Repository not authorized")
    if not (1 <= max_total_chars <= 24000) or len(paths) > 8:
        raise ValueError("Context budget exceeded")
    info = api.repository(owner, repo)
    branch = next((b for b in api.branches(owner, repo)
                   if b["name"] == info["default_branch"]), None)
    if branch is None:
        raise ValueError("Default branch missing")
    commit = branch["commit_id"]
    listing = create_codebase_map(api.tree(owner, repo, commit),
                                  owner=owner, repository=repo, commit_sha=commit)
    allowed = {item["path"] for item in listing["files"]}
    if any(p not in allowed for p in paths):
        raise ValueError("File not in pinned source map")
    files = []
    remaining = max_total_chars
    for path in dict.fromkeys(paths):
        result = get_source_context(api, owner, repo, commit, path)
        size = len(result["text"])
        if size > remaining:
            break
        remaining -= size
        files.append({"path": path, "text": result["text"], "source_commit": commit})
    return {"schema": "orion.qwen-gitea-context/1", "repository": allowed_repository,
            "source_commit": commit, "available_file_count": listing["file_count"],
            "files": files, "trust": "untrusted_source", "authority": "context_only",
            "may_execute": False, "may_write": False}
