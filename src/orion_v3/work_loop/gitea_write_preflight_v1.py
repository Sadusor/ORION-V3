"""Gitea write request preflight: independent of the existing read-only API.

No HTTP, Git, secrets, or write execution. Only creates a bounded intent
that a future ORION-authorized executor may consume after independent checks.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit
import re


_BRANCH = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$")
_SHA = re.compile(r"^[0-9a-f]{40}$")
_FORBIDDEN = frozenset({"main", "master", "HEAD"})


@dataclass(frozen=True, slots=True)
class GiteaWriteIntent:
    project_id: str
    task_id: str
    repository: str
    branch: str
    expected_base_sha: str
    operation: str


def build_write_intent(
    *,
    project_id: str,
    task_id: str,
    repository: str,
    branch: str,
    expected_base_sha: str,
    operation: str,
) -> GiteaWriteIntent:
    """Fail closed for writes outside a task-scoped non-protected branch."""
    for field in (project_id, task_id, repository):
        if not isinstance(field, str) or not field.strip() or field != field.strip():
            raise ValueError("missing or malformed scope")
    if any(x in repository for x in ("..", "\\", ":", "@")) or repository.count("/") != 1:
        raise ValueError("repository must be owner/name")
    if not all(re.fullmatch(r"[A-Za-z0-9_.-]+", x) for x in repository.split("/")):
        raise ValueError("invalid repository")
    if not isinstance(branch, str) or not _BRANCH.fullmatch(branch):
        raise ValueError("invalid branch")
    if (branch in _FORBIDDEN or branch.startswith(("/", "-", ".")) or
            branch.endswith(("/", ".", ".lock")) or
            "//" in branch or ".." in branch or "@{" in branch or "\\" in branch):
        raise ValueError("protected or malformed branch")
    if not branch.startswith("orion/tasks/"):
        raise ValueError("writes must target task branches")
    if not isinstance(expected_base_sha, str) or not _SHA.fullmatch(expected_base_sha):
        raise ValueError("exact base commit required")
    if operation not in ("create_branch", "commit_files"):
        raise ValueError("operation not allowed")
    return GiteaWriteIntent(project_id, task_id, repository, branch, expected_base_sha, operation)


def validate_write_endpoint(url: str) -> str:
    """Reject credentials, plain HTTP outside loopback, fragments and query."""
    if not isinstance(url, str):
        raise ValueError("invalid endpoint")
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ValueError("invalid endpoint")
    if parts.username is not None or parts.password is not None or parts.query or parts.fragment:
        raise ValueError("credentials/query/fragment forbidden")
    if parts.scheme == "http" and parts.hostname not in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("non-local HTTP forbidden")
    if parts.path.rstrip("/") not in ("", "/api/v1"):
        raise ValueError("endpoint must be Gitea API root")
    return url.rstrip("/")
