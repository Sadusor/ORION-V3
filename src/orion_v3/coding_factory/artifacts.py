from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


class ArtifactStoreError(RuntimeError):
    pass


@dataclass(frozen=True)
class ArtifactRef:
    artifact_id: str
    sha256: str
    size_bytes: int


class ArtifactStore:
    """Content-addressed immutable artifact bytes.

    The SHA-256 is the identity. Existing content is reused. Reads always
    re-hash bytes so accidental/direct filesystem mutation is detected.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put_bytes(self, data: bytes) -> ArtifactRef:
        if not isinstance(data, bytes):
            raise ArtifactStoreError("artifact data must be bytes")
        digest = hashlib.sha256(data).hexdigest()
        path = self._path(digest)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            existing = path.read_bytes()
            if hashlib.sha256(existing).hexdigest() != digest:
                raise ArtifactStoreError("existing artifact hash mismatch")
            if existing != data:
                raise ArtifactStoreError("artifact digest collision")
        else:
            try:
                with path.open("xb") as handle:
                    handle.write(data)
            except FileExistsError:
                existing = path.read_bytes()
                if existing != data:
                    raise ArtifactStoreError("concurrent artifact mismatch")
        return ArtifactRef(
            artifact_id=digest,
            sha256=digest,
            size_bytes=len(data),
        )

    def put_text(self, text: str) -> ArtifactRef:
        if not isinstance(text, str):
            raise ArtifactStoreError("artifact text must be string")
        return self.put_bytes(text.encode("utf-8"))

    def read_bytes(self, artifact_id: str) -> bytes:
        self._validate_id(artifact_id)
        path = self._path(artifact_id)
        if not path.is_file():
            raise ArtifactStoreError("artifact does not exist")
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest != artifact_id:
            raise ArtifactStoreError("artifact integrity check failed")
        return data

    def read_text(self, artifact_id: str) -> str:
        return self.read_bytes(artifact_id).decode("utf-8")

    def exists(self, artifact_id: str) -> bool:
        try:
            self._validate_id(artifact_id)
        except ArtifactStoreError:
            return False
        path = self._path(artifact_id)
        if not path.is_file():
            return False
        try:
            return hashlib.sha256(path.read_bytes()).hexdigest() == artifact_id
        except OSError:
            return False

    def storage_path(self, artifact_id: str) -> Path:
        self._validate_id(artifact_id)
        return self._path(artifact_id)

    def _path(self, digest: str) -> Path:
        return self.root / digest[:2] / digest[2:4] / (digest + ".blob")

    @staticmethod
    def _validate_id(value: str) -> None:
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(ch not in "0123456789abcdef" for ch in value)
        ):
            raise ArtifactStoreError("invalid artifact id")
