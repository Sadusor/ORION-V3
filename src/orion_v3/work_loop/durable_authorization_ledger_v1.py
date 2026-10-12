"""Durable SQLite nonce reservation for future governed write execution.

No network writes or authority decisions occur here. The caller must first
verify ORION authorization, policy, revision, and STOP. Reserve a nonce
before attempting a side effect; never roll it back on failed execution.
"""
from __future__ import annotations

import re
from contextlib import closing
import sqlite3
from pathlib import Path

_NONCE = re.compile(r"^[0-9a-f]{32}$")
_SHA = re.compile(r"^[0-9a-f]{64}$")


class DurableAuthorizationLedger:
    def __init__(self, database_path: str | Path):
        self._path = Path(database_path)
        if str(self._path) == ":memory:":
            raise ValueError("in-memory ledger is not durable")
        if not self._path.parent.is_dir():
            raise ValueError("ledger directory must already exist")
        with closing(self._connect()) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS used_authorizations (
                nonce TEXT PRIMARY KEY,
                proposal_hash TEXT NOT NULL,
                source_revision TEXT NOT NULL,
                reserved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(str(self._path), timeout=10, isolation_level=None)
        db.execute("PRAGMA busy_timeout=10000")
        db.execute("PRAGMA synchronous=FULL")
        return db

    def reserve(self, *, nonce: str, proposal_hash: str, source_revision: str) -> bool:
        if not isinstance(nonce, str) or not _NONCE.fullmatch(nonce):
            raise ValueError("invalid authorization nonce")
        if not isinstance(proposal_hash, str) or not _SHA.fullmatch(proposal_hash):
            raise ValueError("invalid proposal hash")
        if not isinstance(source_revision, str) or not re.fullmatch(r"[0-9a-f]{40}", source_revision):
            raise ValueError("invalid source revision")
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                db.execute(
                    "INSERT INTO used_authorizations (nonce, proposal_hash, source_revision) VALUES (?, ?, ?)",
                    (nonce, proposal_hash, source_revision),
                )
                db.execute("COMMIT")
                return True
            except sqlite3.IntegrityError:
                db.execute("ROLLBACK")
                return False
            except BaseException:
                db.execute("ROLLBACK")
                raise

    def contains(self, nonce: str) -> bool:
        if not isinstance(nonce, str) or not _NONCE.fullmatch(nonce):
            raise ValueError("invalid authorization nonce")
        with closing(self._connect()) as db:
            return db.execute("SELECT 1 FROM used_authorizations WHERE nonce=?", (nonce,)).fetchone() is not None
