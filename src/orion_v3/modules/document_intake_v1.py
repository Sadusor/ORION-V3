"""Authenticated document-to-index intake, isolated from canonical memory."""
from __future__ import annotations

import base64
import binascii
from pathlib import Path

from .document_index_v1 import DocumentIndexV1, extract_document_text

MAX_BYTES = 2_000_000
EXTENSIONS = {".txt", ".md", ".csv", ".json", ".log"}


def import_indexed_document(*, state_dir, project: str, filename: str, data_base64: str) -> dict:
    if not isinstance(project, str) or not project.strip() or len(project) > 120:
        raise ValueError("Explicit project required")
    if not isinstance(filename, str) or not filename or len(filename) > 255:
        raise ValueError("Invalid document name")
    if filename != Path(filename).name or "/" in filename or "\\" in filename:
        raise ValueError("Document name must not include directories")
    if Path(filename).suffix.lower() not in EXTENSIONS:
        raise ValueError("Supported text documents: txt, md, csv, json, log")
    if not isinstance(data_base64, str) or len(data_base64) > (MAX_BYTES * 4 // 3 + 16):
        raise ValueError("Document exceeds size limit")
    try:
        raw = base64.b64decode(data_base64, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("Invalid document payload") from exc
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError("Document must be non-empty and no larger than 2 MB")
    pages = extract_document_text(raw, filename)
    root = Path(state_dir)
    if not root.is_dir():
        raise ValueError("State directory unavailable")
    result = DocumentIndexV1(root / "indexed_documents.sqlite3").ingest_text(
        project=project, filename=filename, content="", pages=pages
    )
    return {"ok": True, **result}
