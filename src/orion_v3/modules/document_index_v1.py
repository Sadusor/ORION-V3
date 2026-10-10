"""Owner-scoped, disposable FTS5 index for uploaded document text.

No automatic canonical memory promotion. File extraction never executes macros or
embedded instructions. Caller authenticates upload and controls staging paths.
"""
from __future__ import annotations
from contextlib import closing
from pathlib import Path
import hashlib
import re
import sqlite3

class DocumentIndexV1:
    def __init__(self, db_path: str | Path):
        self.path=Path(db_path)
        if not self.path.parent.is_dir():
            raise ValueError("Document index directory must exist")
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS document_fts USING fts5(
                project UNINDEXED, document_id UNINDEXED, filename UNINDEXED,
                page UNINDEXED, part UNINDEXED, text,
                tokenize='unicode61 remove_diacritics 2')""")
    def ingest_text(self, *, project: str, filename: str, content: str,
                    pages: list[tuple[int,str]] | None = None) -> dict:
        if not project or len(project)>120 or not filename or len(filename)>255:
            raise ValueError("Explicit bounded project and document name required")
        sections=pages if pages is not None else [(1,content)]
        if not sections or len(sections)>1000:
            raise ValueError("Document has no supported pages or exceeds page limit")
        if sum(len(t) for _,t in sections)>2_000_000:
            raise ValueError("Document text budget exceeded")
        digest=hashlib.sha256((filename+"\0"+str(sections)).encode("utf-8")).hexdigest()
        rows=[]
        for number,text in sections:
            if not isinstance(number,int) or number<1 or not isinstance(text,str):
                raise ValueError("Invalid page text")
            for pos in range(0,len(text),1800):
                rows.append((project,digest,filename,str(number),str(pos//1800),text[pos:pos+1800]))
        with closing(sqlite3.connect(self.path,timeout=10)) as db, db:
            db.execute("DELETE FROM document_fts WHERE project=? AND filename=?",(project,filename))
            db.executemany("INSERT INTO document_fts VALUES(?,?,?,?,?,?)",rows)
        return {"document_id":digest,"project":project,"filename":filename,"chunks":len(rows),
                "trust":"untrusted_document","authority":"context_only"}
    def search(self, query: str, *, project: str, limit: int=8) -> list[dict]:
        if not project or len(project)>120:
            raise ValueError("Explicit project required")
        if not query or len(query)>500:
            return []
        terms=re.findall(r"[^\W_]+",query,flags=re.UNICODE)[:16]
        if not terms:return []
        expression=" OR ".join('"' + t.replace('"','""') + '"' for t in terms)
        with closing(sqlite3.connect(self.path)) as db:
            rows=db.execute("""SELECT document_id,filename,page,part,text,bm25(document_fts)
                FROM document_fts WHERE document_fts MATCH ? AND project=?
                ORDER BY bm25(document_fts) LIMIT ?""",
                (expression,project,min(max(int(limit),1),12))).fetchall()
        return [{"document_id":id,"filename":file,"page":int(page),"part":int(part),
                 "snippet":text,"score":score,"trust":"untrusted_document",
                 "authority":"context_only"} for id,file,page,part,text,score in rows]

def extract_document_text(data: bytes, filename: str) -> list[tuple[int,str]]:
    """Accept limited text formats or PDFs using optional PyMuPDF. Fail closed otherwise."""
    if len(data)>15_000_000:
        raise ValueError("Document upload exceeds size limit")
    suffix=Path(filename).suffix.lower()
    if suffix in {".txt",".md",".csv",".json",".py",".log"}:
        return [(1,data.decode("utf-8-sig",errors="strict"))]
    if suffix==".pdf":
        try: import fitz
        except ImportError as exc: raise RuntimeError("PDF support requires PyMuPDF") from exc
        pages=[]
        with fitz.open(stream=data,filetype="pdf") as pdf:
            if pdf.needs_pass or len(pdf)>1000:
                raise ValueError("Encrypted or oversized PDF unsupported")
            for number,page in enumerate(pdf):
                pages.append((number+1,page.get_text("text")))
        if not any(text.strip() for _,text in pages):
            raise ValueError("Scanned PDF requires separate OCR approval")
        return pages
    raise ValueError("Unsupported document format")
