"""Bounded read-only authorized Gitea repository search. Additive to frozen ORION retrieval."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from contextlib import closing
import re
import sqlite3
from .gitea_code_index_v1 import GiteaCodeIndex
from .gitea_codebase_map_v1 import create_codebase_map
from .gitea_source_context_v2 import get_source_context_v2
from .gitea_relevance_v2 import search_relevant_context
from .universal_retrieval_v1 import KnowledgeHit

ELIGIBLE = frozenset({".md",".py",".js",".ts",".tsx",".cs",".kt",".json",".yaml",".yml",".ps1",".html",".css"})
MAX_FILES = 500
_VALID = re.compile(r"^[a-zA-Z0-9_.-]{1,100}$")

@dataclass(frozen=True)
class AuthorizedRepo:
    alias: str
    owner: str
    name: str
    project: str

class GiteaMultiRepoV1:
    """Injected authorization and Gitea reader; no credentials or catalog loaded here."""
    def __init__(self, *, api, state_dir, catalog: tuple[AuthorizedRepo,...]):
        self.api = api
        self.root = Path(state_dir)
        if not self.root.is_dir() or not catalog or len(catalog)>64:
            raise ValueError("Invalid index directory or bounded catalog")
        self.by_alias = {}
        self.by_project = {}
        self.by_name = {}
        for entry in catalog:
            if not all(_VALID.fullmatch(s or "") for s in
                       (entry.alias,entry.owner,entry.name,entry.project)):
                raise ValueError("Unsafe catalog entry")
            alias = entry.alias.casefold()
            repository = (entry.owner+"/"+entry.name).casefold()
            if alias in self.by_alias or entry.project in self.by_project:
                raise ValueError("Duplicate alias or project")
            self.by_alias[alias] = entry
            self.by_project[entry.project] = entry
            for key in (entry.name.casefold(),repository):
                self.by_name.setdefault(key,[]).append(entry)
        self.index_path = self.root / "gitea-code-index-v2-full.sqlite3"

    def resolve(self, name):
        key = str(name or "").strip().casefold()
        if key in self.by_alias:
            return self.by_alias[key]
        matches = self.by_name.get(key,[])
        if len(matches)==1:
            return matches[0]
        raise ValueError("No unique authorized repository match")

    def authorized_inventory(self):
        return tuple(sorted(self.by_alias.values(),key=lambda r:r.alias.casefold()))

    def visible_inventory(self, *, max_pages=40, page_size=25, owner="MyGitea"):
        """Bounded authenticated inventory; do not confuse user and owner scopes.

        A small requested page size avoids a Gitea maximum-response cap being
        mistaken for the final page. No automatic source authorization.
        """
        if not 1 <= max_pages <= 100 or not 1 <= page_size <= 25:
            raise ValueError("Unsafe inventory pagination")
        paths = {
            "authenticated_user": lambda p: f"user/repos?page={p}&limit={page_size}",
            "owner_account": lambda p: f"users/{owner}/repos?page={p}&limit={page_size}",
        }
        scopes = {}
        union = {}
        for label, endpoint in paths.items():
            seen = set()
            count = 0
            complete = False
            error = None
            try:
                for page in range(1, max_pages + 1):
                    raw = self.api._get(endpoint(page))
                    if not isinstance(raw, list):
                        raise ValueError("Unexpected repository response")
                    for item in raw:
                        key = (item["owner"]["login"], item["name"])
                        if key in seen:
                            raise ValueError("Duplicate repository within scope")
                        seen.add(key)
                        union[key] = {"owner": key[0], "name": key[1]}
                        count += 1
                    if len(raw) < page_size:
                        complete = True
                        break
            except (OSError, ValueError, RuntimeError, KeyError, TypeError):
                error = "listing_unavailable"
            scopes[label] = {"count": count, "complete": complete, "error": error}
        return {"count": len(union), "complete": all(v["complete"] for v in scopes.values()),
                "repositories": sorted(union.values(), key=lambda x: (x["owner"], x["name"])),
                "scopes": scopes, "scope": "authenticated user and owner account; not instance-wide"}

    def refresh(self, repo):
        """Refresh only explicitly authorized repository at exact live default-branch SHA."""
        if self.by_project.get(repo.project)!=repo:
            raise PermissionError("Repository not authorized")
        info=self.api.repository(repo.owner,repo.name)
        if info["owner"].casefold()!=repo.owner.casefold() or info["name"].casefold()!=repo.name.casefold():
            raise ValueError("Gitea repository identity mismatch")
        branch=info["default_branch"]
        branches=self.api.branches(repo.owner,repo.name)
        commits=[b["commit_id"] for b in branches if b["name"]==branch]
        if len(commits)!=1:
            raise ValueError("Default branch not available")
        commit=commits[0]
        repository=repo.owner+"/"+repo.name
        index=GiteaCodeIndex(self.index_path)
        with closing(sqlite3.connect(self.index_path)) as db:
            current=db.execute("SELECT commit_sha FROM code_revision WHERE project=? AND repository=?",
                              (repo.project,repository)).fetchone()
        if current and current[0]==commit:
            return {"commit":commit,"refreshed":False,"repository":repository}
        listing=create_codebase_map(self.api.tree(repo.owner,repo.name,commit),
                                    owner=repo.owner,repository=repo.name,commit_sha=commit)
        paths=[f["path"] for f in listing["files"] if f["extension"] in ELIGIBLE]
        if not paths or len(paths)>MAX_FILES:
            raise ValueError("Repository has no eligible files or exceeds indexing limit")
        files=[];skipped=[]
        for path in paths:
            try:
                item=get_source_context_v2(self.api,repo.owner,repo.name,commit,path)
                files.append({"path":path,"text":item["text"],"source_commit":commit})
            except (ValueError,UnicodeError):
                skipped.append(path)
        if not files:
            raise ValueError("No readable source files")
        index.rebuild(project=repo.project,repository=repository,commit_sha=commit,
                      files=files,max_files=MAX_FILES)
        return {"commit":commit,"refreshed":True,"repository":repository,
                "indexed_files":len(files),"skipped_files":len(skipped)}

    def search(self,query,*,project,limit):
        if project not in self.by_project:
            raise ValueError("Project is not authorized")
        if not isinstance(query,str) or not query.strip() or len(query)>300 or not 1<=limit<=24:
            raise ValueError("Invalid bounded query")
        repo=self.by_project[project]
        revision=self.refresh(repo)
        result=search_relevant_context(self.index_path,query=query,project=repo.project,
                    repository=revision["repository"],commit_sha=revision["commit"],max_chars=6000)
        hits=[]
        for i,part in enumerate(result["results"][:limit]):
            file=part["path"]; chunk=part["part"]; sha=revision["commit"]
            citation=f"MyGitea2 {revision['repository']} {sha} {file} part {chunk}"
            hits.append(KnowledgeHit(source="mygitea2",project=project,
               identifier=f"{revision['repository']}:{sha}:{file}:{chunk}",
               snippet=f"Repository: {revision['repository']}\nFile: {file}\nCommit: {sha}\n{part['text']}",
               citation=citation,score=float(limit-i)))
        return hits
