"""SQLite transaction mutex across processes; independent of Python threads."""
from __future__ import annotations
from contextlib import contextmanager
from pathlib import Path
import sqlite3


@contextmanager
def exclusive_vault_lock(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(root / "VAULT_LOCK.sqlite3", timeout=10, isolation_level=None)
    try:
        connection.execute("BEGIN IMMEDIATE")
        yield
        connection.execute("COMMIT")
    except BaseException:
        connection.execute("ROLLBACK")
        raise
    finally:
        connection.close()
