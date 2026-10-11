"""Unactivated project-scoped archive device credential store.

A separately enrolled credential is required; ordinary pairing tokens are
not automatically accepted. Stored values are SHA-256 digests, never plaintext.
This module grants no owner deletion authority and changes no live server.
"""
from __future__ import annotations
import hashlib
import hmac
import secrets
import sqlite3
from contextlib import closing
from pathlib import Path


class ProjectDeviceCredentialsV1:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as db, db:
            db.execute("""CREATE TABLE IF NOT EXISTS scoped_credentials(
                digest TEXT PRIMARY KEY, project_id TEXT NOT NULL,
                revoked INTEGER NOT NULL DEFAULT 0)""")

    def _connect(self):
        return sqlite3.connect(str(self.path), timeout=10)

    def enroll(self, *, project_id: str, physically_confirmed: bool = False) -> str:
        if not physically_confirmed:
            raise PermissionError("Physical owner enrollment is required")
        if not isinstance(project_id, str) or not project_id.strip() or len(project_id) > 160:
            raise ValueError("Invalid project")
        secret = secrets.token_urlsafe(48)
        digest = hashlib.sha256(secret.encode("utf-8")).hexdigest()
        with closing(self._connect()) as db, db:
            db.execute("INSERT INTO scoped_credentials(digest,project_id) VALUES (?,?)",
                       (digest, project_id))
        return secret

    def authorized(self, token: str, project_id: str) -> bool:
        if not isinstance(token, str) or len(token) < 32:
            return False
        if not isinstance(project_id, str) or not project_id.strip():
            return False
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        with closing(self._connect()) as db:
            row = db.execute("SELECT project_id,revoked FROM scoped_credentials WHERE digest=?",
                             (digest,)).fetchone()
        return row is not None and row[1] == 0 and hmac.compare_digest(row[0], project_id)

    def revoke(self, token: str, *, physically_confirmed: bool = False) -> bool:
        if not physically_confirmed:
            raise PermissionError("Physical owner revocation is required")
        if not isinstance(token, str) or len(token) < 32:
            return False
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        with closing(self._connect()) as db, db:
            cursor = db.execute("UPDATE scoped_credentials SET revoked=1 WHERE digest=?",
                                (digest,))
            return cursor.rowcount > 0
