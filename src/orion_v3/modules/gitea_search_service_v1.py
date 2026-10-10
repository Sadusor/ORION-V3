"""Opt-in, read-only MyGitea2 FTS5 search service for authorized ORION project.

Indexes are disposable in isolated ORION storage; never modify Gitea, canonical
memory, or frozen brain pipeline. Caller validates owner/session authorization.
"""
from __future__ import annotations
from pathlib import Path
from .gitea_readonly_v1 import GiteaReadonly
from .gitea_codebase_map_v1 import create_codebase_map
from .gitea_source_context_v1 import get_source_context
from .gitea_code_index_v1 import GiteaCodeIndex
from .gitea_search_context_v1 import search_code_context

def search_live_gitea(*, query: str, project_id: str,
                      state_dir: str | Path, api: GiteaReadonly | None = None) -> dict:
    if project_id != "orion-v3":
        raise PermissionError("Project not approved for Gitea search")
    if not query or len(query) > 300:
        raise ValueError("Invalid query")
    root = Path(state_dir)
    if not root.is_dir():
        raise ValueError("Derived index directory must already exist")
    gitea = api or GiteaReadonly("http://127.0.0.1:3001")
    owner, name = "MyGitea", "ORION-V3"
    repo = gitea.repository(owner,name)
    branch = next((b for b in gitea.branches(owner,name)
                   if b["name"] == repo["default_branch"]),None)
    if branch is None:
        raise ValueError("Default branch unavailable")
    commit = branch["commit_id"]
    listing = create_codebase_map(gitea.tree(owner,name,commit),
        owner=owner,repository=name,commit_sha=commit)
    paths = [item["path"] for item in listing["files"] if item["extension"] in {".py",".md",".js"}]
    if not paths:
        raise ValueError("No searchable files")
    files = []
    for path in paths[:40]:
        try:
            source = get_source_context(gitea,owner,name,commit,path)
        except ValueError:
            continue
        files.append({"path":path,"text":source["text"],"source_commit":commit})
    if not files:
        raise ValueError("No source text available")
    index=GiteaCodeIndex(root/"gitea-code-index-v1.sqlite3")
    index.rebuild(project=project_id,repository="MyGitea/ORION-V3",commit_sha=commit,files=files)
    result=search_code_context(index.path,query=query,project=project_id,
        repository="MyGitea/ORION-V3",commit_sha=commit,max_chars=6000)
    result["indexed_files"]=len(files)
    result["partial_coverage"]=len(paths)>len(files)
    return result
