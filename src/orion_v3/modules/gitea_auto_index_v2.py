"""Commit-aware MyGitea2 search. Derived cache only; no canonical-memory writes."""
from __future__ import annotations
from pathlib import Path
import sqlite3
from contextlib import closing
from .gitea_readonly_v1 import GiteaReadonly
from .gitea_codebase_map_v1 import create_codebase_map
from .gitea_source_context_v1 import get_source_context
from .gitea_code_index_v1 import GiteaCodeIndex
from .gitea_search_context_v1 import search_code_context

PROJECT = "orion-v3"
REPOSITORY = "MyGitea/ORION-V3"
MAX_FILES = 500

def refresh_current_index(*, state_dir, api=None):
    """One refresh per new default-branch commit; reject incomplete coverage."""
    root = Path(state_dir)
    if not root.is_dir():
        raise ValueError("Index parent directory missing")
    gitea = api or GiteaReadonly("http://127.0.0.1:3001")
    owner, repo = "MyGitea", "ORION-V3"
    identity = gitea.repository(owner, repo)
    branch = identity["default_branch"]
    matches = [b for b in gitea.branches(owner, repo) if b["name"] == branch]
    if len(matches) != 1:
        raise ValueError("Gitea default branch unavailable")
    commit = matches[0]["commit_id"]
    path = root / "gitea-code-index-v2.sqlite3"
    index = GiteaCodeIndex(path)
    with closing(sqlite3.connect(path)) as db:
        revision = db.execute("SELECT commit_sha FROM code_revision WHERE project=? AND repository=?",
                              (PROJECT, REPOSITORY)).fetchone()
    if revision and revision[0] == commit:
        return {"commit":commit,"refreshed":False,"path":path}
    mapping = create_codebase_map(gitea.tree(owner, repo, commit),
                                   owner=owner, repository=repo, commit_sha=commit)
    candidates = [f["path"] for f in mapping["files"] if f["extension"] in {".md",".py",".js",".ts",".tsx",".cs",".kt",".json",".yaml",".yml",".ps1",".html",".css"}]
    if len(candidates) > MAX_FILES:
        raise ValueError("Too many searchable files for bounded V2 index; preserve previous revision")
    files=[]
    skipped=[]
    for name in candidates:
        try:
            entry = get_source_context(gitea, owner, repo, commit, name)
        except (ValueError, UnicodeError):
            skipped.append(name)
            continue
        files.append({"path":name,"text":entry["text"],"source_commit":commit})
    if not files:
        raise ValueError("No eligible Gitea content")
    index.rebuild(project=PROJECT,repository=REPOSITORY,commit_sha=commit,files=files,max_files=MAX_FILES)
    return {"commit":commit,"refreshed":True,"path":path,"indexed_files":len(files),
            "eligible_files":len(candidates),"skipped_files":len(skipped),"partial_coverage":bool(skipped)}

def search_live_gitea_v2(*, query, project_id, state_dir, api=None):
    if project_id != PROJECT:
        raise PermissionError("Project not approved")
    if not query or len(query)>300:
        raise ValueError("Invalid query")
    info=refresh_current_index(state_dir=state_dir,api=api)
    response=search_code_context(info["path"],query=query,project=PROJECT,
                                 repository=REPOSITORY,commit_sha=info["commit"],max_chars=6000)
    response.update({k:v for k,v in info.items() if k not in {"path"}})
    return response
