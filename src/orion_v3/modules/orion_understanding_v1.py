"""ORION Understanding V1: advisory, deterministic query interpretation.

Donor-inspired design: DSPy structured intent, Haystack query expansion,
Zoekt source-path/symbol signals, Ragas evaluation. No donor runtime imports.
Does not choose authorization scope, execute tools, or modify canonical state.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

_WORDS = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")
_FILLER = frozenset(("search find show tell me what which where how can does do did we you our my the a an in on at for from of with across repositories repository repos mygitea2 gitea code source files file include paths names references please locate identify are there exists exist").split())
_CONCEPTS = (
    (frozenset(("ui", "interface", "screen", "screens", "frontend", "front", "visual", "layout", "controls", "control", "widgets", "widget")), ("ui", "interface", "controls")),
    (frozenset(("button", "buttons", "click", "clicked", "press", "pressed", "tap", "tapped", "action", "actions", "controls", "control")), ("button", "onclick", "click")),
    (frozenset(("history", "conversation", "conversations", "chats")), ("history", "chat")),
    (frozenset(("android", "mobile", "phone", "apk")), ("android", "mobile")),
    (frozenset(("windows", "desktop", "pc", "wpf")), ("windows", "desktop")),
    (frozenset(("database", "databases", "db", "sqlite", "sql", "schema", "table", "tables", "column", "columns")), ("sql", "schema", "database", "table")),
)

@dataclass(frozen=True)
class Understanding:
    owner_request: str
    search_query: str
    concepts: tuple[str, ...]
    intent: str


def interpret(owner_request: str) -> Understanding:
    """Produce bounded search terms; original owner text remains authoritative."""
    request = str(owner_request or "")[:1000]
    tokens = [t.casefold() for t in _WORDS.findall(request)]
    meaningful = []
    for term in tokens:
        if term not in _FILLER and term not in meaningful:
            meaningful.append(term)
    concepts = []
    for triggers, expansions in _CONCEPTS:
        if any(t in triggers for t in tokens):
            for term in expansions:
                if term not in meaningful:
                    meaningful.append(term)
                if term not in concepts:
                    concepts.append(term)
    query = " ".join(meaningful[:12]) or " ".join(tokens[:12])
    intent = "source_lookup" if any(t in tokens for t in (
        "code", "source", "implemented", "implementation", "built", "where",
        "files", "file", "functions", "function", "controls", "buttons",
        "database", "databases", "sql", "schema", "table", "tables", "sqlite",
    )) else "general"
    return Understanding(request, query, tuple(concepts), intent)


def rank_source_path(path: str, *, concepts: tuple[str, ...]) -> int:
    """Advisory path relevance; prioritize requested implementation over generic storage."""
    p = str(path or "").replace("\\\\", "/").casefold()
    score = 0
    if p.startswith("tests/") or "/tests/" in p or "_test." in p or ".test." in p:
        score -= 25
    if p.startswith("docs/") or p.endswith(".md"):
        score -= 15
    if p.endswith((".js", ".ts", ".tsx", ".kt", ".cs", ".html", ".css", ".sql")):
        score += 2
    ui_intent = any(t in concepts for t in ("ui", "interface", "controls"))
    button_intent = any(t in concepts for t in ("button", "onclick", "click"))
    if ui_intent:
        if p.startswith("ui/") or "/ui/" in p:
            score += 18
        elif p.startswith("android/"):
            score += 3
    database_intent = any(t in concepts for t in ("sql", "schema", "database", "table"))
    if button_intent and not database_intent:
        if any(t in p for t in ("button", "control", "action", "workspace")):
            score += 12
        if any(t in p for t in ("history", "chat")):
            score += 2
        if any(t in p for t in ("store", "storage", "database", "bridge")):
            score -= 8
    if database_intent:
        if p.endswith(".sql") or any(t in p for t in ("schema", "database", "sqlite", "sql", "store")):
            score += 18
        if p.endswith(".md"):
            score -= 6
    return score


def rank_unique_paths(paths: list[str], *, concepts: tuple[str, ...], limit: int = 10) -> list[str]:
    """Avoid one chunked source file monopolizing the evidence budget."""
    unique = set(paths)
    return sorted(unique, key=lambda p: (-rank_source_path(p, concepts=concepts), p))[:limit]
