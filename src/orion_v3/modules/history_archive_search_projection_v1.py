"""Replaceable searchable projection of HistoryArchive, never canonical memory.

Read-only from source; indexes only non-deleted archive messages. Never
promotes memories. Project scope is mandatory. Explicit refresh is required
until integrated with the production write boundary.
"""
from __future__ import annotations
import sqlite3
from contextlib import closing
from pathlib import Path

class ArchiveSearchProjectionV1:
    def __init__(self, archive_path, index_path):
        self.archive_path=Path(archive_path)
        self.index_path=Path(index_path)
        if self.archive_path.resolve()==self.index_path.resolve():
            raise ValueError("Index must be separate from archive")
        self.index_path.parent.mkdir(parents=True,exist_ok=True)
        with closing(sqlite3.connect(self.index_path)) as db, db:
            db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS archive_fts USING fts5(project_id UNINDEXED,conversation_id UNINDEXED,message_id UNINDEXED,text)")
            db.execute("CREATE TABLE IF NOT EXISTS projection_state (id INTEGER PRIMARY KEY CHECK(id=1), updated INTEGER NOT NULL)")

    def refresh(self):
        if not self.archive_path.is_file():
            raise FileNotFoundError(self.archive_path)
        src=sqlite3.connect("file:"+str(self.archive_path.resolve()).replace("\\","/")+"?mode=ro",uri=True)
        try:
            rows=src.execute("""SELECT m.project_id,m.conversation_id,m.message_id,m.text
                FROM messages AS m JOIN conversations AS c ON c.id=m.conversation_id
                WHERE c.deleted_at_ms IS NULL AND m.project_id=c.project_id
                ORDER BY m.conversation_id,m.message_id""").fetchall()
            with closing(sqlite3.connect(self.index_path)) as db, db:
                db.execute("DELETE FROM archive_fts")
                db.executemany("INSERT INTO archive_fts(project_id,conversation_id,message_id,text) VALUES (?,?,?,?)",rows)
                db.execute("INSERT OR REPLACE INTO projection_state(id,updated) VALUES(1,strftime('%s','now'))")
            return len(rows)
        finally:
            src.close()

    def search(self,*,project_id,query,limit=12):
        if not isinstance(project_id,str) or not project_id.strip() or len(project_id)>160:
            raise ValueError("Project scope required")
        if not isinstance(query,str) or not query.strip() or len(query)>200:
            raise ValueError("Bounded query required")
        if type(limit) is not int or not 1<=limit<=12:
            raise ValueError("Limit out of range")
        with closing(sqlite3.connect(self.index_path)) as db:
            return [{"conversation_id":r[0],"message_id":r[1],"text":r[2]}
                for r in db.execute("""SELECT conversation_id,message_id,text
                    FROM archive_fts WHERE archive_fts MATCH ? AND project_id=?
                    ORDER BY rank LIMIT ?""",(query,project_id,limit)).fetchall()]
