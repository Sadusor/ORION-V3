"""Durable, single-use authorization nonce claims for simulated Work Hand.

SQLite UNIQUE primary key serializes claims across processes. Claims are
consumed BEFORE work. A crash wastes the capability (fail closed).
"""
from __future__ import annotations

from pathlib import Path
import sqlite3


class NonceStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def consume(self, nonce: str) -> bool:
        if not isinstance(nonce, str) or len(nonce) != 32:
            return False
        try:
            with sqlite3.connect(self.path, timeout=5) as db:
                db.execute("CREATE TABLE IF NOT EXISTS used_nonces (nonce TEXT PRIMARY KEY)")
                db.execute("INSERT INTO used_nonces(nonce) VALUES (?)", (nonce,))
            return True
        except (sqlite3.IntegrityError, sqlite3.OperationalError):
            return False
