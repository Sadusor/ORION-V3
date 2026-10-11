"""C5 isolated owner capability with independently provisioned random secret.

Not installed in product_server. The capability is NOT a pairing token.
A caller must verify it server-side before invoking destructive routes.
"""
from __future__ import annotations
import hashlib
import hmac
import os
import secrets
import threading
from pathlib import Path


class OwnerCapabilityV1:
    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "owner_delete_capability.sha256"
        self._lock = threading.RLock()

    @staticmethod
    def _digest(secret: str) -> str:
        return hashlib.sha256(secret.encode("utf-8")).hexdigest()

    def enrolled(self) -> bool:
        return self.path.is_file()

    def enroll(self, *, physically_confirmed: bool = False) -> str:
        if not physically_confirmed:
            raise PermissionError("Owner physical enrollment required")
        with self._lock:
            if self.path.exists():
                raise FileExistsError("Already enrolled; use explicit rotation")
            secret = secrets.token_urlsafe(48)
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            fd = os.open(str(self.path), flags, 0o600)
            try:
                with os.fdopen(fd, "w", encoding="ascii") as file:
                    file.write(self._digest(secret) + "\n")
                    file.flush()
                    os.fsync(file.fileno())
            except BaseException:
                try:
                    self.path.unlink()
                except OSError:
                    pass
                raise
            return secret

    def verify(self, secret: str) -> bool:
        if not isinstance(secret, str) or len(secret) < 32:
            return False
        with self._lock:
            try:
                expected = self.path.read_text(encoding="ascii").strip()
            except FileNotFoundError:
                return False
            return len(expected) == 64 and hmac.compare_digest(
                self._digest(secret), expected)

    def revoke(self, *, physically_confirmed: bool = False):
        if not physically_confirmed:
            raise PermissionError("Owner physical revocation required")
        with self._lock:
            self.path.unlink(missing_ok=True)

    def rotate(self, *, current_secret: str, physically_confirmed: bool = False) -> str:
        if not physically_confirmed or not self.verify(current_secret):
            raise PermissionError("Owner physical rotation and current secret required")
        with self._lock:
            new_secret = secrets.token_urlsafe(48)
            replacement = self.path.with_suffix(".next")
            try:
                with replacement.open("x", encoding="ascii") as file:
                    file.write(self._digest(new_secret) + "\n")
                    file.flush()
                    os.fsync(file.fileno())
                os.replace(replacement, self.path)
            finally:
                replacement.unlink(missing_ok=True)
            return new_secret
