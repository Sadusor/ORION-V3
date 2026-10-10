"""Disposable, project-scoped SQLite FTS5 index of Gitea source snippets.

No canonical memory access, no Gitea writes. Source remains untrusted.
"""
from __future__ import annotations
from contextlib import closing
from pathlib import Path
import re
import sqlite3

SHA = re.compile(r"^[0-9a-fA-F]{40}$")
TOKEN = re.compile(r"[^\W_]+|[A-Za-z_][A-Za-z_0-9]*", re.UNICODE)

class GiteaCodeIndex:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        if not self.path.parent.is_dir():
            raise ValueError("Index parent directory missing")
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS code_fts USING fts5(
                project UNINDEXED, repository UNINDEXED, commit_sha UNINDEXED,
                path UNINDEXED, part UNINDEXED, text,
                tokenize='unicode61 remove_diacritics 2')""")
            db.execute("""CREATE TABLE IF NOT EXISTS code_revision(
                project TEXT NOT NULL, repository TEXT NOT NULL,
                commit_sha TEXT NOT NULL, PRIMARY KEY(project,repository))""")

    def rebuild(self, *, project: str, repository: str, commit_sha: str,
                files: list[dict], max_files: int = 500, chunk_chars: int = 1800) -> int:
        if not project or not repository or not SHA.fullmatch(commit_sha):
            raise ValueError("Project, repository, full commit SHA required")
        if not 1 <= len(files) <= max_files or not 256 <= chunk_chars <= 4000:
            raise ValueError("Index input bounds exceeded")
        rows=[]
        for f in files:
            path=f.get("path")
            content=f.get("text")
            if not isinstance(path,str) or not isinstance(content,str) or not path or len(path)>500:
                raise ValueError("Invalid file entry")
            if f.get("source_commit") != commit_sha:
                raise ValueError("Mixed source commits")
            if len(content)>65536:
                raise ValueError("Oversized file")
            for i in range(0,len(content),chunk_chars):
                rows.append((project,repository,commit_sha,path,str(i//chunk_chars),content[i:i+chunk_chars]))
        with closing(sqlite3.connect(self.path,timeout=10)) as db, db:
            db.execute("DELETE FROM code_fts WHERE project=? AND repository=?",(project,repository))
            db.executemany("INSERT INTO code_fts VALUES(?,?,?,?,?,?)",rows)
            db.execute("INSERT OR REPLACE INTO code_revision VALUES(?,?,?)",(project,repository,commit_sha))
        return len(rows)

    def search(self, query: str, *, project: str, repository: str,
               commit_sha: str, limit: int = 8) -> list[dict]:
        if not project or not repository or not SHA.fullmatch(commit_sha):
            raise ValueError("Explicit authorized scope and exact commit required")
        if len(query)>500:
            return []
        terms=TOKEN.findall(query)[:16]
        if not terms:
            return []
        expression=" OR ".join('"' + term.replace('"','""') + '"' for term in terms)
        with closing(sqlite3.connect(self.path,timeout=10)) as db:
            current=db.execute("SELECT commit_sha FROM code_revision WHERE project=? AND repository=?",(project,repository)).fetchone()
            if current is None or current[0]!=commit_sha:
                raise ValueError("Index stale or missing for requested commit")
            rows=db.execute("""SELECT path,part,text,bm25(code_fts) FROM code_fts
                WHERE code_fts MATCH ? AND project=? AND repository=? AND commit_sha=?
                ORDER BY bm25(code_fts) LIMIT ?""",
                (expression,project,repository,commit_sha,min(max(1,limit),12))).fetchall()
        return [{"path":p,"part":int(n),"snippet":t,"score":score,
                 "repository":repository,"source_commit":commit_sha,
                 "trust":"untrusted_source"} for p,n,t,score in rows]
