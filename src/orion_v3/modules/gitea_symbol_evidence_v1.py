"""Read-only, commit-pinned source-symbol evidence enrichment for Gitea chat.

Derived FTS cache only. No canonical memory or repository mutation.
"""
from __future__ import annotations

from contextlib import closing
import re
import sqlite3


def enrich_symbol_evidence(index_path, response, *, query, project, repository,
                           commit_sha, max_chars=6000):
    """Prioritize implementation chunks and adjacent chunks within the same file."""
    words = set(re.findall(r"[a-z0-9]+", query.casefold()))
    intent = bool(words & {"file", "implement", "implements", "implementation",
                           "button", "function", "code", "source", "where"})
    if not intent:
        return response
    terms = {w for w in words if len(w) >= 4 and w not in {
        "which", "where", "what", "does", "file", "implement", "implements",
        "implementation", "button", "source", "code", "within", "from",
        "mygitea2", "orion", "that", "this", "function"}}
    if not terms:
        return response
    with closing(sqlite3.connect(index_path)) as db:
        revision = db.execute(
            "SELECT commit_sha FROM code_revision WHERE project=? AND repository=?",
            (project, repository)).fetchone()
        if revision is None or revision[0] != commit_sha:
            raise ValueError("Gitea index revision mismatch")
        rows = db.execute(
            "SELECT path,part,text FROM code_fts WHERE project=? AND repository=? "
            "AND commit_sha=? ORDER BY path,cast(part AS INTEGER)",
            (project, repository, commit_sha)).fetchall()
    # Exact indexed source only; score source filenames and code, not prose claims.
    candidates = []
    for path, part, body in rows:
        p = path.casefold()
        b = body.casefold()
        path_matches = sum(t in p for t in terms)
        code_matches = sum(t in b for t in terms)
        if not (path_matches or code_matches):
            continue
        source_code = p.endswith((".py", ".js", ".ts", ".tsx", ".kt", ".cs", ".ps1"))
        symbol_hits = sum(bool(re.search(r"(?<![a-z0-9])" + re.escape(t) +
                                         r"[a-z0-9_]*", b)) for t in terms)
        score = 8 * path_matches + 4 * code_matches + 2 * symbol_hits + (3 if source_code else 0)
        candidates.append((score, path, int(part), body))
    candidates.sort(key=lambda x: (-x[0], x[1], x[2]))
    by_key = {(p, int(n)): body for p, n, body in rows}
    chosen = []
    seen = set()
    remaining = max_chars
    for score, path, part, body in candidates[:20]:
        for n in (part, part - 1, part + 1):
            key = (path, n)
            chunk = by_key.get(key)
            if chunk is None or key in seen or len(chunk) > remaining:
                continue
            chosen.append({"path": path, "part": n,
                           "source_commit": commit_sha, "text": chunk})
            seen.add(key)
            remaining -= len(chunk)
        if remaining < 400:
            break
    for item in response.get("results", []):
        key = (item["path"], int(item["part"]))
        if key not in seen and len(item["text"]) <= remaining:
            chosen.append(item)
            seen.add(key)
            remaining -= len(item["text"])
    result = dict(response)
    result["results"] = chosen
    return result
