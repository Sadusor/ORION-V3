"""Read-only adapter from indexed documents to UniversalRetrievalV1.

Never ingests, promotes, mutates memory, opens arbitrary databases, or widens
project scope. The caller chooses a trusted local index path and project.
"""
from __future__ import annotations

from pathlib import Path

from .document_index_v1 import DocumentIndexV1
from .universal_retrieval_v1 import KnowledgeHit


def document_knowledge_source(index_path: str | Path):
    """Create an explicit-project retrieval adapter for an existing FTS index."""
    path = Path(index_path)
    if not path.is_file():
        raise FileNotFoundError("Indexed document database is unavailable")

    def search(*, query: str, project: str, limit: int) -> list[KnowledgeHit]:
        if not project or not project.strip():
            raise ValueError("Explicit document project required")
        results = DocumentIndexV1(path).search(query, project=project, limit=limit)
        return [
            KnowledgeHit(
                source="documents",
                identifier=f"{hit['document_id']}:{hit['page']}:{hit['part']}",
                snippet=hit["snippet"],
                citation=f"Document {hit['filename']} page {hit['page']} part {hit['part']}",
                project=project,
                score=float(len(results) - i),
            )
            for i, hit in enumerate(results)
        ]

    return search
