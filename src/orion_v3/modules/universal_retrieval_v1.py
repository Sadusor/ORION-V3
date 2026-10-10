"""Unified, provenance-preserving read-only retrieval over replaceable sources.

Adapters are called only for the explicit scope; each is responsible for its own
permissions. No automatic memory promotion, ingestion or execution.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class KnowledgeHit:
    source: str
    identifier: str
    snippet: str
    citation: str
    project: str
    score: float = 0.0
    trust: str = "context_only"

class UniversalRetrievalV1:
    def __init__(self):
        self._sources: dict[str, Callable[..., list[KnowledgeHit]]] = {}

    def register(self, name: str, search: Callable[..., list[KnowledgeHit]]) -> None:
        if not name or not name.replace("_", "").isalnum() or name in self._sources:
            raise ValueError("Invalid or duplicate source")
        if not callable(search):
            raise TypeError("Search adapter must be callable")
        self._sources[name] = search

    def retrieve(self, query: str, *, project: str, max_hits: int = 12,
                 max_chars: int = 6000) -> dict:
        if not query.strip() or not project.strip():
            raise ValueError("Query and explicit project required")
        if len(query) > 1000 or not 1 <= max_hits <= 24 or not 100 <= max_chars <= 24000:
            raise ValueError("Retrieval limits exceeded")
        hits = []
        failed = []
        for name, search in self._sources.items():
            try:
                candidates = search(query=query, project=project, limit=max_hits)
                for h in candidates[:max_hits]:
                    if not isinstance(h, KnowledgeHit) or h.project != project or h.source != name:
                        raise ValueError("Invalid adapter provenance or scope")
                    if h.trust != "context_only" or not h.identifier or not h.citation:
                        raise ValueError("Missing provenance or unsafe trust")
                    hits.append(h)
            except (ValueError, OSError, RuntimeError) as exc:
                failed.append({"source":name,"error":type(exc).__name__})
        hits.sort(key=lambda h:(-h.score,h.source,h.identifier))
        results=[]; seen=set(); remaining=max_chars
        for h in hits:
            key=(h.source,h.identifier)
            if key in seen or len(results)>=max_hits:
                continue
            if len(h.snippet)>remaining:
                continue
            seen.add(key); remaining-=len(h.snippet)
            results.append({"source":h.source,"identifier":h.identifier,
                            "snippet":h.snippet,"citation":h.citation,
                            "project":h.project,"trust":"context_only"})
        return {"schema":"orion.universal-retrieval/1","project":project,
                "results":results,"source_errors":failed,
                "authority":"context_only","may_write":False,"may_execute":False}
