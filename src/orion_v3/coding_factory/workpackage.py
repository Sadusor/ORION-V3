from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import PurePosixPath
from typing import Any, Iterable, Mapping

from .artifacts import ArtifactStore


class WorkPackageError(ValueError):
    pass


class ArtifactKind(str, Enum):
    PATCH = "PATCH"
    FILE = "FILE"


class FileOperation(str, Enum):
    CREATE = "CREATE"
    REPLACE = "REPLACE"


@dataclass(frozen=True)
class PackageArtifact:
    kind: ArtifactKind
    artifact_id: str
    sha256: str
    size_bytes: int
    relative_path: str | None = None
    operation: FileOperation | None = None
    target_paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkPackage:
    package_id: str
    project_id: str
    task_id: str
    attempt_id: str
    base_sha: str
    coder_provider: str
    coder_model: str
    prompt_sha256: str
    response_sha256: str
    artifacts: tuple[PackageArtifact, ...]
    allowed_paths: tuple[str, ...]
    forbidden_paths: tuple[str, ...]
    verifier_spec: Mapping[str, Any]
    package_sha256: str
    manifest_artifact_id: str


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_relpath(path: str) -> str:
    if not isinstance(path, str):
        raise WorkPackageError("path must be string")
    raw = path.replace("\\", "/").strip()
    if not raw or raw.startswith("/") or re.match(r"^[A-Za-z]:", raw):
        raise WorkPackageError("path must be project-relative")
    pure = PurePosixPath(raw)
    if any(part in {"", ".", ".."} for part in pure.parts):
        raise WorkPackageError("path contains unsafe segment")
    if pure.parts and pure.parts[0].lower() == ".git":
        raise WorkPackageError(".git paths are forbidden")
    return str(pure)


def _validate_git_sha(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value):
        raise WorkPackageError("base_sha must be lowercase 40-char Git SHA")
    return value


class WorkPackageFactory:
    def __init__(self, artifact_store: ArtifactStore) -> None:
        self.artifact_store = artifact_store

    def file_artifact(
        self,
        relative_path: str,
        text: str,
        *,
        operation: FileOperation,
    ) -> PackageArtifact:
        path = _normalize_relpath(relative_path)
        ref = self.artifact_store.put_text(text)
        return PackageArtifact(
            kind=ArtifactKind.FILE,
            artifact_id=ref.artifact_id,
            sha256=ref.sha256,
            size_bytes=ref.size_bytes,
            relative_path=path,
            operation=operation,
        )

    def patch_artifact(
        self,
        patch_text: str,
        *,
        target_paths: Iterable[str],
    ) -> PackageArtifact:
        if not isinstance(patch_text, str) or not patch_text.strip():
            raise WorkPackageError("patch text must be non-empty")
        targets = tuple(sorted({_normalize_relpath(p) for p in target_paths}))
        if not targets:
            raise WorkPackageError("PATCH artifact requires declared target paths")
        ref = self.artifact_store.put_text(patch_text)
        return PackageArtifact(
            kind=ArtifactKind.PATCH,
            artifact_id=ref.artifact_id,
            sha256=ref.sha256,
            size_bytes=ref.size_bytes,
            target_paths=targets,
        )

    def create(
        self,
        *,
        project_id: str,
        task_id: str,
        attempt_id: str,
        base_sha: str,
        coder_provider: str,
        coder_model: str,
        prompt_text: str,
        response_text: str,
        artifacts: Iterable[PackageArtifact],
        allowed_paths: Iterable[str],
        forbidden_paths: Iterable[str],
        verifier_spec: Mapping[str, Any],
    ) -> WorkPackage:
        project_id = self._nonempty(project_id, "project_id")
        task_id = self._nonempty(task_id, "task_id")
        attempt_id = self._nonempty(attempt_id, "attempt_id")
        base_sha = _validate_git_sha(base_sha)
        coder_provider = self._nonempty(coder_provider, "coder_provider")
        coder_model = self._nonempty(coder_model, "coder_model")
        if not isinstance(prompt_text, str) or not isinstance(response_text, str):
            raise WorkPackageError("prompt/response must be strings")
        if not isinstance(verifier_spec, Mapping):
            raise WorkPackageError("verifier_spec must be object")

        allowed = tuple(sorted({_normalize_relpath(p) for p in allowed_paths}))
        forbidden = tuple(sorted({_normalize_relpath(p) for p in forbidden_paths}))
        if not allowed:
            raise WorkPackageError("at least one allowed path is required")

        normalized = tuple(
            self._validate_artifact(item, allowed, forbidden) for item in artifacts
        )
        if not normalized:
            raise WorkPackageError("package requires at least one artifact")

        body = {
            "schema": "orion.workpackage.v0",
            "project_id": project_id,
            "task_id": task_id,
            "attempt_id": attempt_id,
            "base_sha": base_sha,
            "coder_provider": coder_provider,
            "coder_model": coder_model,
            "prompt_sha256": _hash_text(prompt_text),
            "response_sha256": _hash_text(response_text),
            "artifacts": [self._artifact_dict(item) for item in normalized],
            "allowed_paths": list(allowed),
            "forbidden_paths": list(forbidden),
            "verifier_spec": dict(verifier_spec),
        }
        package_sha = hashlib.sha256(
            _canonical_json(body).encode("utf-8")
        ).hexdigest()
        manifest = dict(body)
        manifest["package_id"] = package_sha
        manifest["package_sha256"] = package_sha
        manifest_ref = self.artifact_store.put_text(_canonical_json(manifest))

        return WorkPackage(
            package_id=package_sha,
            project_id=project_id,
            task_id=task_id,
            attempt_id=attempt_id,
            base_sha=base_sha,
            coder_provider=coder_provider,
            coder_model=coder_model,
            prompt_sha256=body["prompt_sha256"],
            response_sha256=body["response_sha256"],
            artifacts=normalized,
            allowed_paths=allowed,
            forbidden_paths=forbidden,
            verifier_spec=dict(verifier_spec),
            package_sha256=package_sha,
            manifest_artifact_id=manifest_ref.artifact_id,
        )

    def load(self, manifest_artifact_id: str) -> WorkPackage:
        manifest = json.loads(self.artifact_store.read_text(manifest_artifact_id))
        if manifest.get("schema") != "orion.workpackage.v0":
            raise WorkPackageError("unsupported manifest schema")
        unsigned = {
            key: value
            for key, value in manifest.items()
            if key not in {"package_id", "package_sha256"}
        }
        actual_sha = hashlib.sha256(
            _canonical_json(unsigned).encode("utf-8")
        ).hexdigest()
        if (
            manifest.get("package_id") != actual_sha
            or manifest.get("package_sha256") != actual_sha
        ):
            raise WorkPackageError("manifest package hash mismatch")

        artifacts = tuple(
            PackageArtifact(
                kind=ArtifactKind(item["kind"]),
                artifact_id=item["artifact_id"],
                sha256=item["sha256"],
                size_bytes=int(item["size_bytes"]),
                relative_path=item.get("relative_path"),
                operation=(
                    FileOperation(item["operation"])
                    if item.get("operation") else None
                ),
                target_paths=tuple(item.get("target_paths") or ()),
            )
            for item in manifest["artifacts"]
        )
        package = WorkPackage(
            package_id=actual_sha,
            project_id=manifest["project_id"],
            task_id=manifest["task_id"],
            attempt_id=manifest["attempt_id"],
            base_sha=manifest["base_sha"],
            coder_provider=manifest["coder_provider"],
            coder_model=manifest["coder_model"],
            prompt_sha256=manifest["prompt_sha256"],
            response_sha256=manifest["response_sha256"],
            artifacts=artifacts,
            allowed_paths=tuple(manifest["allowed_paths"]),
            forbidden_paths=tuple(manifest["forbidden_paths"]),
            verifier_spec=dict(manifest["verifier_spec"]),
            package_sha256=actual_sha,
            manifest_artifact_id=manifest_artifact_id,
        )
        _validate_git_sha(package.base_sha)
        for artifact in package.artifacts:
            self._validate_artifact(
                artifact, package.allowed_paths, package.forbidden_paths
            )
        return package

    def _validate_artifact(
        self,
        item: PackageArtifact,
        allowed: tuple[str, ...],
        forbidden: tuple[str, ...],
    ) -> PackageArtifact:
        if not isinstance(item, PackageArtifact):
            raise WorkPackageError("artifact must be PackageArtifact")
        if item.artifact_id != item.sha256:
            raise WorkPackageError("artifact identity/hash mismatch")
        if not self.artifact_store.exists(item.artifact_id):
            raise WorkPackageError("artifact bytes missing or corrupt")
        if len(self.artifact_store.read_bytes(item.artifact_id)) != item.size_bytes:
            raise WorkPackageError("artifact size mismatch")

        if item.kind == ArtifactKind.FILE:
            if item.relative_path is None or item.operation is None:
                raise WorkPackageError("FILE artifact requires path and operation")
            path = _normalize_relpath(item.relative_path)
            self._require_allowed(path, allowed, forbidden)
            return PackageArtifact(
                kind=item.kind,
                artifact_id=item.artifact_id,
                sha256=item.sha256,
                size_bytes=item.size_bytes,
                relative_path=path,
                operation=item.operation,
                target_paths=(),
            )

        if item.kind == ArtifactKind.PATCH:
            if item.relative_path is not None or item.operation is not None:
                raise WorkPackageError("PATCH artifact cannot carry file operation")
            targets = tuple(sorted({_normalize_relpath(p) for p in item.target_paths}))
            if not targets:
                raise WorkPackageError("PATCH artifact requires declared target paths")
            for path in targets:
                self._require_allowed(path, allowed, forbidden)
            return PackageArtifact(
                kind=item.kind,
                artifact_id=item.artifact_id,
                sha256=item.sha256,
                size_bytes=item.size_bytes,
                target_paths=targets,
            )

        raise WorkPackageError("unsupported artifact kind")

    @staticmethod
    def _require_allowed(
        path: str,
        allowed: tuple[str, ...],
        forbidden: tuple[str, ...],
    ) -> None:
        def under(candidate: str, root: str) -> bool:
            return candidate == root or candidate.startswith(root.rstrip("/") + "/")

        if not any(under(path, root) for root in allowed):
            raise WorkPackageError("artifact path outside allowed paths")
        if any(under(path, root) for root in forbidden):
            raise WorkPackageError("artifact path inside forbidden paths")

    @staticmethod
    def _nonempty(value: str, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise WorkPackageError(f"{field} must be non-empty")
        return value.strip()

    @staticmethod
    def _artifact_dict(item: PackageArtifact) -> dict[str, Any]:
        return {
            "kind": item.kind.value,
            "artifact_id": item.artifact_id,
            "sha256": item.sha256,
            "size_bytes": item.size_bytes,
            "relative_path": item.relative_path,
            "operation": item.operation.value if item.operation else None,
            "target_paths": list(item.target_paths),
        }
