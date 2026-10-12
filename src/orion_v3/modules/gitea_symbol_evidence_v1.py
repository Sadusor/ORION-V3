"""Read-only, commit-pinned, file-level source evidence for ORION chat."""
from __future__ import annotations

from collections import defaultdict
from contextlib import closing
import re
import sqlite3


_CAMEL = re.compile(r"([a-z0-9])([A-Z])")
_ACRONYM = re.compile(r"([A-Z]+)([A-Z][a-z])")
_STOP = {
    "which", "where", "what", "does", "file", "implement",
    "implements", "implementation", "the", "in", "mygitea2",
    "orion", "source", "code", "from", "this", "that"
}
_CODE_EXT = (".py", ".js", ".ts", ".tsx", ".kt", ".cs", ".ps1")


def _words(value):
    value = _ACRONYM.sub(r"\1 \2", value)
    value = _CAMEL.sub(r"\1 \2", value)
    return set(re.findall(r"[a-z0-9]+", value.casefold()))


def _matching_lines(text, terms):
    return [
        line.strip()
        for line in text.splitlines()
        if _words(line) & terms
    ]


def enrich_symbol_evidence(
    index_path, response, *, query, project, repository,
    commit_sha, max_chars=6000
):
    """Pack matching source lines into commit-pinned file dossiers."""
    words = _words(query)

    intent = bool(words & {
        "file", "implement", "implements", "implementation",
        "button", "function", "code", "source", "where",
        "sync", "refresh", "find", "defined", "endpoint"
    })

    terms = {
        word for word in words
        if len(word) >= 3 and word not in _STOP
    }

    if not intent or not terms:
        return response

    with closing(sqlite3.connect(index_path)) as db:
        revision = db.execute(
            "SELECT commit_sha FROM code_revision "
            "WHERE project=? AND repository=?",
            (project, repository)
        ).fetchone()

        if revision is None or revision[0] != commit_sha:
            raise ValueError("Gitea index revision mismatch")

        rows = db.execute(
            "SELECT path,part,text FROM code_fts "
            "WHERE project=? AND repository=? AND commit_sha=? "
            "ORDER BY path,cast(part AS INTEGER)",
            (project, repository, commit_sha)
        ).fetchall()

    by_file = defaultdict(list)

    for path, part, body in rows:
        lines = _matching_lines(body, terms)

        if lines or (_words(path) & terms):
            by_file[path].append((int(part), lines))

    if not by_file:
        return response

    def score(path):
        groups = by_file[path]
        lines = [
            line
            for _, matches in groups
            for line in matches
        ]

        declarations = sum(
            bool(re.search(
                r"(?:id=|function |def |async |const |let |var )",
                line, re.I
            ))
            for line in lines
        )

        endpoint = any("/api/" in line for line in lines)
        ui = any(
            re.search(r"(?:button|refresh|click)", line, re.I)
            for line in lines
        )

        code = path.casefold().endswith(_CODE_EXT)
        source_terms = {"sync", "button"}
        coverage = sum(any(term in _words(line) for line in lines) for term in source_terms)
        path_relevance = 8 if any(word in _words(path) for word in terms) else 0

        return (
            (80 if code else -40)
            + coverage * 35
            + path_relevance
            + declarations * 3
            + (12 if endpoint else 0)
            + (12 if ui else 0)
            + len(groups)
        )

    ranked = sorted(
        by_file,
        key=lambda path: (-score(path), path)
    )

    chosen = []
    remaining = max_chars

    for path in ranked[:3]:
        header = (
            "FILE: " + path + "\n"
            "COMMIT: " + commit_sha + "\n"
        )

        if len(header) >= remaining:
            break

        lines = []
        seen = set()

        for part, matches in sorted(by_file[path]):
            for line in matches:
                if line not in seen:
                    seen.add(line)
                    lines.append(
                        "Part " + str(part) + ": " + line[:300]
                    )

        if not lines:
            continue

        dossier = header

        for line in lines:
            if len(dossier) + len(line) + 1 > remaining:
                break

            dossier += line + "\n"

        chosen.append({
            "path": path,
            "part": 0,
            "source_commit": commit_sha,
            "text": dossier
        })

        remaining -= len(dossier)

    if not chosen:
        return response

    result = dict(response)
    result["results"] = chosen
    return result