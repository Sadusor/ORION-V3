"""Experimental shared STOP authority serialized with the real Vault SQLite lock.

Not wired into production. STOP is monotonic and fail-closed.
"""
import sqlite3
from contextlib import closing
from pathlib import Path
from orion_v3.work_loop.vault_lock import exclusive_vault_lock

class SharedStop:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.db = self.root / "STOP_AUTHORITY.sqlite3"

    def _read(self):
        if not self.db.is_file():
            raise RuntimeError("STOP authority missing")
        with closing(sqlite3.connect(self.db, timeout=10)) as c:
            row = c.execute("SELECT stopped FROM authority WHERE id=1").fetchone()
            if row is None or row[0] not in (0,1):
                raise RuntimeError("STOP authority corrupt")
            return bool(row[0])

    def initialize(self):
        with exclusive_vault_lock(self.root):
            if self.db.exists():
                self._read()
                return
            with closing(sqlite3.connect(self.db)) as c, c:
                c.execute("CREATE TABLE authority(id INTEGER PRIMARY KEY CHECK(id=1), stopped INTEGER NOT NULL CHECK(stopped IN (0,1)))")
                c.execute("INSERT INTO authority VALUES(1,0)")

    def stop(self):
        with exclusive_vault_lock(self.root):
            with closing(sqlite3.connect(self.db)) as c, c:
                updated=c.execute("UPDATE authority SET stopped=1 WHERE id=1").rowcount
                if updated != 1: raise RuntimeError("STOP authority unavailable")

    def stop_requested(self):
        return self._read()

    def commit_guard(self):
        return not self.stop_requested()
