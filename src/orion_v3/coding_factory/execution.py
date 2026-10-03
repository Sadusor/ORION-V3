from __future__ import annotations

import hashlib
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from orion_v3.state import (
    AttemptAuthority,
    AttemptDenied,
    EventRecord,
    EventType,
    OrionStateStore,
)

from .artifacts import ArtifactStore
from .workpackage import (
    ArtifactKind,
    FileOperation,
    WorkPackage,
    WorkPackageFactory,
)


class ExecutionDenied(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass
class PreparedExecution:
    package: WorkPackage
    action_event_id: str
    worktree: Path
    git_subcommands: list[str]


@dataclass(frozen=True)
class ExecutionEvidence:
    package_id: str
    package_sha256: str
    attempt_id: str
    lease_generation: int
    base_sha: str
    changed_paths: tuple[str, ...]
    diff_sha256: str
    result_tree_sha: str
    verifier: Mapping[str, Any]
    git_subcommands: tuple[str, ...]


class WorkPackageExecutor:
    """Contained exact-SHA Git execution for one authorized immutable WorkPackage."""

    def __init__(
        self,
        *,
        store: OrionStateStore,
        attempts: AttemptAuthority,
        factory: WorkPackageFactory,
        source_repo: Path,
        worktree_root: Path,
    ) -> None:
        self.store = store
        self.attempts = attempts
        self.factory = factory
        self.artifacts: ArtifactStore = factory.artifact_store
        self.source_repo = Path(source_repo).resolve()
        self.worktree_root = Path(worktree_root).resolve()
        self.worktree_root.mkdir(parents=True, exist_ok=True)

    def prepare(
        self,
        *,
        manifest_artifact_id: str,
        expected_package_sha256: str,
        action_event_id: str,
        lease_token: str | None,
    ) -> PreparedExecution:
        package = self.factory.load(manifest_artifact_id)
        if package.package_sha256 != expected_package_sha256:
            raise ExecutionDenied("package_hash_mismatch", "WorkPackage hash is not the approved hash.")

        attempt = self.attempts.validate(package.attempt_id, lease_token)
        self._require_attempt_package(attempt, package)
        self._require_execution_action(action_event_id, package, attempt)

        commands: list[str] = []
        try:
            resolved = self._git(
                self.source_repo,
                ["rev-parse", "--verify", f"{package.base_sha}^{{commit}}"],
                commands,
            ).strip()
            if resolved != package.base_sha:
                raise ExecutionDenied("base_sha_mismatch", "Approved base SHA did not resolve exactly.")
        except ExecutionDenied:
            raise
        except Exception as exc:
            raise ExecutionDenied("base_sha_unavailable", "Approved base SHA is unavailable.") from exc

        target = self.worktree_root / (
            f"{package.attempt_id}-{package.package_id[:12]}-{uuid4().hex[:8]}"
        )
        if target.exists():
            raise ExecutionDenied("worktree_collision", "Disposable worktree path already exists.")

        try:
            self._git(
                self.source_repo,
                ["worktree", "add", "--detach", str(target), package.base_sha],
                commands,
            )
            head = self._git(target, ["rev-parse", "HEAD"], commands).strip()
            if head != package.base_sha:
                raise ExecutionDenied("worktree_head_mismatch", "Disposable worktree HEAD is not exact base SHA.")
            dirty = self._git(
                target,
                ["status", "--porcelain=v1", "--untracked-files=all"],
                commands,
            ).strip()
            if dirty:
                raise ExecutionDenied("worktree_not_clean", "Disposable worktree is not clean before effects.")

            self.attempts.checkpoint(
                package.attempt_id,
                lease_token,
                {
                    "phase": "worktree_ready",
                    "package_sha256": package.package_sha256,
                    "base_sha": package.base_sha,
                },
            )
            return PreparedExecution(
                package=package,
                action_event_id=action_event_id,
                worktree=target,
                git_subcommands=commands,
            )
        except Exception:
            self._cleanup_path(target, commands)
            raise

    def continue_execution(
        self,
        prepared: PreparedExecution,
        *,
        lease_token: str | None,
    ) -> ExecutionEvidence:
        package = prepared.package
        try:
            attempt = self.attempts.validate(package.attempt_id, lease_token)
            self._require_attempt_package(attempt, package)
            self._require_execution_action(prepared.action_event_id, package, attempt)

            for artifact in package.artifacts:
                self.attempts.validate(package.attempt_id, lease_token)
                if artifact.kind == ArtifactKind.FILE:
                    self._apply_file(prepared.worktree, artifact)
                elif artifact.kind == ArtifactKind.PATCH:
                    patch = self.artifacts.read_text(artifact.artifact_id)
                    self._git(
                        prepared.worktree,
                        ["apply", "--check", "--whitespace=nowarn", "-"],
                        prepared.git_subcommands,
                        input_text=patch,
                    )
                    self.attempts.validate(package.attempt_id, lease_token)
                    self._git(
                        prepared.worktree,
                        ["apply", "--whitespace=nowarn", "-"],
                        prepared.git_subcommands,
                        input_text=patch,
                    )
                else:
                    raise ExecutionDenied("unsupported_artifact", "Unsupported WorkPackage artifact.")

            self.attempts.validate(package.attempt_id, lease_token)
            self._git(prepared.worktree, ["add", "-A"], prepared.git_subcommands)
            changed = tuple(
                p
                for p in self._git(
                    prepared.worktree,
                    ["diff", "--cached", "--name-only", "HEAD", "--"],
                    prepared.git_subcommands,
                ).splitlines()
                if p.strip()
            )
            if not changed:
                raise ExecutionDenied("no_effect", "WorkPackage produced no Git-visible change.")
            self._require_changed_paths(package, changed)

            diff_text = self._git(
                prepared.worktree,
                ["diff", "--cached", "--binary", "--no-ext-diff", "HEAD", "--"],
                prepared.git_subcommands,
            )
            diff_sha = hashlib.sha256(diff_text.encode("utf-8")).hexdigest()
            tree_sha = self._git(
                prepared.worktree,
                ["write-tree"],
                prepared.git_subcommands,
            ).strip()
            if len(tree_sha) != 40:
                raise ExecutionDenied("invalid_tree_evidence", "Git did not return a tree SHA.")

            verifier = self._run_verifier(package, prepared.worktree)
            checkpoint = {
                "phase": "verified",
                "package_sha256": package.package_sha256,
                "changed_paths": list(changed),
                "diff_sha256": diff_sha,
                "result_tree_sha": tree_sha,
                "verifier": dict(verifier),
            }
            self.attempts.checkpoint(package.attempt_id, lease_token, checkpoint)
            final_attempt = self.attempts.finish(
                package.attempt_id,
                lease_token,
                status="SUCCEEDED",
                result=checkpoint,
            )

            evidence_event = self.store.append_event(
                package.project_id,
                EventType.EVIDENCE,
                checkpoint,
                actor_kind="verifier",
                actor_id="git-worktree-envelope-v0",
                task_id=package.task_id,
                attempt_id=package.attempt_id,
                parent_event_id=prepared.action_event_id,
            )
            self.store.append_event(
                package.project_id,
                EventType.RESULT,
                {
                    "status": final_attempt.status,
                    "package_sha256": package.package_sha256,
                    "evidence_event_id": evidence_event.event_id,
                },
                actor_kind="orion",
                actor_id="coding_factory_executor",
                task_id=package.task_id,
                attempt_id=package.attempt_id,
                parent_event_id=evidence_event.event_id,
            )

            return ExecutionEvidence(
                package_id=package.package_id,
                package_sha256=package.package_sha256,
                attempt_id=package.attempt_id,
                lease_generation=final_attempt.lease_generation,
                base_sha=package.base_sha,
                changed_paths=changed,
                diff_sha256=diff_sha,
                result_tree_sha=tree_sha,
                verifier=verifier,
                git_subcommands=tuple(prepared.git_subcommands),
            )
        except Exception as exc:
            try:
                current = self.attempts.validate(package.attempt_id, lease_token)
            except AttemptDenied:
                current = None
            if current is not None:
                try:
                    self.attempts.finish(
                        package.attempt_id,
                        lease_token,
                        status="FAILED",
                        result={
                            "phase": "execution_failed",
                            "package_sha256": package.package_sha256,
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                        },
                    )
                except AttemptDenied:
                    pass
            raise
        finally:
            self._cleanup_path(prepared.worktree, prepared.git_subcommands)

    def run(
        self,
        *,
        manifest_artifact_id: str,
        expected_package_sha256: str,
        action_event_id: str,
        lease_token: str | None,
    ) -> ExecutionEvidence:
        prepared = self.prepare(
            manifest_artifact_id=manifest_artifact_id,
            expected_package_sha256=expected_package_sha256,
            action_event_id=action_event_id,
            lease_token=lease_token,
        )
        return self.continue_execution(prepared, lease_token=lease_token)

    def _require_execution_action(
        self,
        action_event_id: str,
        package: WorkPackage,
        attempt: Any,
    ) -> EventRecord:
        event = self.store.get_event(action_event_id)
        if event is None:
            raise ExecutionDenied("missing_execution_authorization", "Execution ACTION does not exist.")
        if (
            event.event_type != EventType.ACTION
            or event.actor_kind != "orion"
            or event.project_id != package.project_id
            or event.task_id != package.task_id
            or event.attempt_id != package.attempt_id
        ):
            raise ExecutionDenied("wrong_execution_authorization", "Execution ACTION is out of scope.")
        body = event.payload.get("body")
        if not isinstance(body, dict):
            raise ExecutionDenied("wrong_execution_authorization", "Execution ACTION body is missing.")
        expected = {
            "kind": "WORKPACKAGE_EXECUTION_AUTHORIZATION",
            "package_id": package.package_id,
            "package_sha256": package.package_sha256,
            "manifest_artifact_id": package.manifest_artifact_id,
            "base_sha": package.base_sha,
            "attempt_id": package.attempt_id,
            "lease_generation": attempt.lease_generation,
            "worker_id": attempt.lease_worker_id,
            "execution_authority": True,
        }
        if any(body.get(key) != value for key, value in expected.items()):
            raise ExecutionDenied(
                "stale_execution_authorization",
                "Execution ACTION is not bound to the current package/lease generation.",
            )
        return event

    @staticmethod
    def _require_attempt_package(attempt: Any, package: WorkPackage) -> None:
        if (
            attempt.attempt_id != package.attempt_id
            or attempt.project_id != package.project_id
            or attempt.task_id != package.task_id
        ):
            raise ExecutionDenied("attempt_package_mismatch", "Attempt does not own this WorkPackage.")

    def _apply_file(self, worktree: Path, artifact: Any) -> None:
        if artifact.relative_path is None or artifact.operation is None:
            raise ExecutionDenied("invalid_file_artifact", "FILE artifact is incomplete.")
        target = self._safe_target(worktree, artifact.relative_path)
        if artifact.operation == FileOperation.CREATE:
            if target.exists() or target.is_symlink():
                raise ExecutionDenied("create_target_exists", "FILE CREATE target already exists.")
            target.parent.mkdir(parents=True, exist_ok=True)
        elif artifact.operation == FileOperation.REPLACE:
            if not target.is_file() or target.is_symlink():
                raise ExecutionDenied("replace_target_invalid", "FILE REPLACE target is not a regular file.")
        else:
            raise ExecutionDenied("unsupported_file_operation", "Unsupported FILE operation.")
        target.write_bytes(self.artifacts.read_bytes(artifact.artifact_id))

    @staticmethod
    def _safe_target(worktree: Path, relative_path: str) -> Path:
        root = worktree.resolve()
        current = root
        parts = Path(relative_path).parts
        for part in parts[:-1]:
            current = current / part
            if current.exists() and current.is_symlink():
                raise ExecutionDenied("symlink_escape", "Artifact path traverses a symlink.")
        target = root.joinpath(*parts)
        resolved = target.resolve(strict=False)
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ExecutionDenied("path_escape", "Artifact path escapes disposable worktree.") from exc
        return target

    @staticmethod
    def _under(path: str, root: str) -> bool:
        root = root.rstrip("/")
        return path == root or path.startswith(root + "/")

    def _require_changed_paths(self, package: WorkPackage, changed: tuple[str, ...]) -> None:
        for raw in changed:
            path = raw.replace("\\", "/")
            if not any(self._under(path, root) for root in package.allowed_paths):
                raise ExecutionDenied("changed_path_out_of_scope", f"Changed path outside allowed scope: {path}")
            if any(self._under(path, root) for root in package.forbidden_paths):
                raise ExecutionDenied("changed_path_forbidden", f"Changed path is forbidden: {path}")

    def _run_verifier(self, package: WorkPackage, worktree: Path) -> dict[str, Any]:
        spec = dict(package.verifier_spec)
        if spec.get("kind") != "file_sha256":
            raise ExecutionDenied("unsupported_verifier", "Only deterministic file_sha256 verifier is allowed in V0.")
        path = str(spec.get("path") or "")
        expected = str(spec.get("sha256") or "")
        if len(expected) != 64 or any(ch not in "0123456789abcdef" for ch in expected):
            raise ExecutionDenied("invalid_verifier", "Verifier sha256 is invalid.")
        target = self._safe_target(worktree, path)
        if not target.is_file() or target.is_symlink():
            raise ExecutionDenied("verifier_target_missing", "Verifier target is not a regular file.")
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != expected:
            raise ExecutionDenied("verifier_failed", "Deterministic file hash verifier failed.")
        return {"kind": "file_sha256", "path": path, "sha256": actual, "status": "PASS"}

    @staticmethod
    def _run_process(
        cwd: Path,
        args: list[str],
        *,
        input_text: str | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        proc = subprocess.run(
            args,
            cwd=str(cwd),
            input=input_text,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if check and proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "git command failed").strip()
            raise ExecutionDenied("git_command_failed", detail)
        return proc

    def _git(
        self,
        cwd: Path,
        args: list[str],
        command_log: list[str],
        *,
        input_text: str | None = None,
    ) -> str:
        if not args:
            raise ValueError("git args required")
        command_log.append(args[0])
        proc = self._run_process(
            cwd,
            ["git", *args],
            input_text=input_text,
        )
        return proc.stdout

    def _cleanup_path(self, target: Path, command_log: list[str]) -> None:
        if target.exists():
            command_log.append("worktree")
            self._run_process(
                self.source_repo,
                ["git", "worktree", "remove", "--force", str(target)],
                check=False,
            )
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        command_log.append("worktree")
        self._run_process(
            self.source_repo,
            ["git", "worktree", "prune"],
            check=False,
        )


__all__ = [
    "ExecutionDenied",
    "ExecutionEvidence",
    "PreparedExecution",
    "WorkPackageExecutor",
]
