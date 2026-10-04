from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping
from uuid import uuid4

from orion_v3.state import OrionStateStore


class RegistryDenied(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class TrustClass(str, Enum):
    OWNER_PROJECT = "owner_project"
    DONOR_REPO = "donor_repo"
    SHARED_OR_CLIENT = "shared_or_client"


class ArchiveState(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class ReadPolicy(str, Enum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"


class WritePolicy(str, Enum):
    DENY = "deny"
    OWNER_APPROVAL = "owner_approval"


@dataclass(frozen=True)
class RegistryProject:
    project_id: str
    name: str
    repo_identity: str | None
    trusted_root: str
    trust_class: TrustClass
    archive_state: ArchiveState
    read_policy: ReadPolicy
    write_policy: WritePolicy
    no_cloud: bool
    license_state: str
    revision: str | None
    version: int
    record_sha256: str
    revision_id: str


@dataclass(frozen=True)
class RegistryGroup:
    group_id: str
    name: str
    member_project_ids: tuple[str, ...]
    version: int
    record_sha256: str
    revision_id: str


@dataclass(frozen=True)
class ResolvedProject:
    project_id: str
    name: str
    repo_identity: str | None
    trust_class: str
    archive_state: str
    no_cloud: bool
    license_state: str
    revision: str | None
    registry_version: int
    registry_sha256: str


@dataclass(frozen=True)
class ScopeResolution:
    scope_token: str
    resolution_id: str
    resolved_at: str
    projects: tuple[ResolvedProject, ...]
    trusted_roots: Mapping[str, str]

    def model_safe(self) -> dict[str, Any]:
        return {
            "schema": "orion.v3.scope-resolution.v0",
            "scope_token": self.scope_token,
            "resolution_id": self.resolution_id,
            "resolved_at": self.resolved_at,
            "project_count": len(self.projects),
            "projects": [
                {
                    "project_id": item.project_id,
                    "name": item.name,
                    "repo_identity": item.repo_identity,
                    "trust_class": item.trust_class,
                    "archive_state": item.archive_state,
                    "no_cloud": item.no_cloud,
                    "license_state": item.license_state,
                    "revision": item.revision,
                    "registry_version": item.registry_version,
                    "registry_sha256": item.registry_sha256,
                }
                for item in self.projects
            ],
        }


_REGISTRY_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS workspace_registry_projects (
    project_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    repo_identity TEXT,
    trusted_root TEXT NOT NULL,
    trust_class TEXT NOT NULL,
    archive_state TEXT NOT NULL,
    read_policy TEXT NOT NULL,
    write_policy TEXT NOT NULL,
    no_cloud INTEGER NOT NULL,
    license_state TEXT NOT NULL,
    revision TEXT,
    version INTEGER NOT NULL,
    record_sha256 TEXT NOT NULL,
    revision_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workspace_registry_project_revisions (
    revision_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    owner_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    previous_revision_id TEXT,
    record_json TEXT NOT NULL,
    record_sha256 TEXT NOT NULL,
    UNIQUE(project_id, version)
);

CREATE TRIGGER IF NOT EXISTS workspace_registry_project_revisions_no_update
BEFORE UPDATE ON workspace_registry_project_revisions
BEGIN
    SELECT RAISE(ABORT, 'ORION registry project revisions are append-only');
END;

CREATE TRIGGER IF NOT EXISTS workspace_registry_project_revisions_no_delete
BEFORE DELETE ON workspace_registry_project_revisions
BEGIN
    SELECT RAISE(ABORT, 'ORION registry project revisions are append-only');
END;

CREATE TABLE IF NOT EXISTS workspace_registry_groups (
    group_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    member_project_ids_json TEXT NOT NULL,
    version INTEGER NOT NULL,
    record_sha256 TEXT NOT NULL,
    revision_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workspace_registry_group_revisions (
    revision_id TEXT PRIMARY KEY,
    group_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    owner_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    previous_revision_id TEXT,
    record_json TEXT NOT NULL,
    record_sha256 TEXT NOT NULL,
    UNIQUE(group_id, version)
);

CREATE TRIGGER IF NOT EXISTS workspace_registry_group_revisions_no_update
BEFORE UPDATE ON workspace_registry_group_revisions
BEGIN
    SELECT RAISE(ABORT, 'ORION registry group revisions are append-only');
END;

CREATE TRIGGER IF NOT EXISTS workspace_registry_group_revisions_no_delete
BEFORE DELETE ON workspace_registry_group_revisions
BEGIN
    SELECT RAISE(ABORT, 'ORION registry group revisions are append-only');
END;
"""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _required(value: str, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise RegistryDenied("invalid_registry_value", field + " must be non-empty")
    return text


def _owner_only(actor_kind: str) -> None:
    if str(actor_kind or "").strip().lower() != "owner":
        raise RegistryDenied(
            "registry_owner_only",
            "Workspace registry mutation is owner-only.",
        )


class WorkspaceRegistry:
    """Canonical owner-managed project/workspace registry.

    Trusted roots are stored locally but never exposed through model-safe scope
    resolution packets.
    """

    def __init__(self, store: OrionStateStore) -> None:
        self.store = store

    def initialize(self) -> None:
        self.store.connect().executescript(_REGISTRY_SCHEMA)
        self.store.connect().commit()

    def upsert_project(
        self,
        *,
        actor_kind: str,
        owner_id: str,
        project_id: str,
        name: str,
        trusted_root: str | Path,
        trust_class: TrustClass,
        repo_identity: str | None = None,
        archive_state: ArchiveState = ArchiveState.ACTIVE,
        read_policy: ReadPolicy = ReadPolicy.ALLOWED,
        write_policy: WritePolicy = WritePolicy.OWNER_APPROVAL,
        no_cloud: bool = False,
        license_state: str = "UNKNOWN",
        revision: str | None = None,
    ) -> RegistryProject:
        _owner_only(actor_kind)
        project_id = _required(project_id, "project_id")
        name = _required(name, "name")
        owner_id = _required(owner_id, "owner_id")
        root = str(Path(trusted_root).resolve())
        license_state = _required(license_state, "license_state")
        repo_identity = str(repo_identity).strip() if repo_identity else None
        revision = str(revision).strip() if revision else None

        conn = self.store.connect()
        current = conn.execute(
            "SELECT * FROM workspace_registry_projects WHERE project_id=?",
            (project_id,),
        ).fetchone()
        version = int(current["version"]) + 1 if current is not None else 1
        previous_revision_id = (
            str(current["revision_id"]) if current is not None else None
        )
        record = {
            "project_id": project_id,
            "name": name,
            "repo_identity": repo_identity,
            "trusted_root": root,
            "trust_class": trust_class.value,
            "archive_state": archive_state.value,
            "read_policy": read_policy.value,
            "write_policy": write_policy.value,
            "no_cloud": bool(no_cloud),
            "license_state": license_state,
            "revision": revision,
            "version": version,
        }
        digest = _sha256(record)
        revision_id = str(uuid4())
        created_at = _utc_now()

        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """
                INSERT INTO workspace_registry_project_revisions(
                    revision_id,project_id,version,owner_id,created_at,
                    previous_revision_id,record_json,record_sha256
                ) VALUES(?,?,?,?,?,?,?,?)
                """,
                (
                    revision_id,
                    project_id,
                    version,
                    owner_id,
                    created_at,
                    previous_revision_id,
                    _canonical_json(record),
                    digest,
                ),
            )
            conn.execute(
                """
                INSERT INTO workspace_registry_projects(
                    project_id,name,repo_identity,trusted_root,trust_class,
                    archive_state,read_policy,write_policy,no_cloud,
                    license_state,revision,version,record_sha256,revision_id
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(project_id) DO UPDATE SET
                    name=excluded.name,
                    repo_identity=excluded.repo_identity,
                    trusted_root=excluded.trusted_root,
                    trust_class=excluded.trust_class,
                    archive_state=excluded.archive_state,
                    read_policy=excluded.read_policy,
                    write_policy=excluded.write_policy,
                    no_cloud=excluded.no_cloud,
                    license_state=excluded.license_state,
                    revision=excluded.revision,
                    version=excluded.version,
                    record_sha256=excluded.record_sha256,
                    revision_id=excluded.revision_id
                """,
                (
                    project_id,
                    name,
                    repo_identity,
                    root,
                    trust_class.value,
                    archive_state.value,
                    read_policy.value,
                    write_policy.value,
                    int(bool(no_cloud)),
                    license_state,
                    revision,
                    version,
                    digest,
                    revision_id,
                ),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise

        return self.get_project(project_id)

    def get_project(self, project_id: str) -> RegistryProject:
        row = self.store.connect().execute(
            "SELECT * FROM workspace_registry_projects WHERE project_id=?",
            (project_id,),
        ).fetchone()
        if row is None:
            raise RegistryDenied(
                "unknown_registered_project",
                "Registered project does not exist.",
            )

        material = {
            "project_id": row["project_id"],
            "name": row["name"],
            "repo_identity": row["repo_identity"],
            "trusted_root": row["trusted_root"],
            "trust_class": row["trust_class"],
            "archive_state": row["archive_state"],
            "read_policy": row["read_policy"],
            "write_policy": row["write_policy"],
            "no_cloud": bool(row["no_cloud"]),
            "license_state": row["license_state"],
            "revision": row["revision"],
            "version": int(row["version"]),
        }
        digest = _sha256(material)
        if digest != row["record_sha256"]:
            raise RegistryDenied(
                "registry_integrity_failure",
                "Current project registry checksum does not match its contents.",
            )
        revision = self.store.connect().execute(
            """
            SELECT record_json,record_sha256 FROM workspace_registry_project_revisions
            WHERE revision_id=? AND project_id=? AND version=?
            """,
            (row["revision_id"], row["project_id"], int(row["version"])),
        ).fetchone()
        if revision is None:
            raise RegistryDenied(
                "registry_integrity_failure",
                "Current project registry revision is missing.",
            )
        if (
            revision["record_sha256"] != digest
            or json.loads(revision["record_json"]) != material
        ):
            raise RegistryDenied(
                "registry_integrity_failure",
                "Current project registry row disagrees with its immutable revision.",
            )

        return RegistryProject(
            project_id=row["project_id"],
            name=row["name"],
            repo_identity=row["repo_identity"],
            trusted_root=row["trusted_root"],
            trust_class=TrustClass(row["trust_class"]),
            archive_state=ArchiveState(row["archive_state"]),
            read_policy=ReadPolicy(row["read_policy"]),
            write_policy=WritePolicy(row["write_policy"]),
            no_cloud=bool(row["no_cloud"]),
            license_state=row["license_state"],
            revision=row["revision"],
            version=int(row["version"]),
            record_sha256=row["record_sha256"],
            revision_id=row["revision_id"],
        )

    def upsert_group(
        self,
        *,
        actor_kind: str,
        owner_id: str,
        group_id: str,
        name: str,
        member_project_ids: Iterable[str],
    ) -> RegistryGroup:
        _owner_only(actor_kind)
        group_id = _required(group_id, "group_id")
        name = _required(name, "name")
        owner_id = _required(owner_id, "owner_id")
        members: list[str] = []
        seen: set[str] = set()
        for raw in member_project_ids:
            project_id = _required(str(raw), "member_project_id")
            if project_id in seen:
                continue
            self.get_project(project_id)
            seen.add(project_id)
            members.append(project_id)
        if not members:
            raise RegistryDenied(
                "invalid_registry_group",
                "Registry group must contain at least one project.",
            )

        conn = self.store.connect()
        current = conn.execute(
            "SELECT * FROM workspace_registry_groups WHERE group_id=?",
            (group_id,),
        ).fetchone()
        version = int(current["version"]) + 1 if current is not None else 1
        previous_revision_id = (
            str(current["revision_id"]) if current is not None else None
        )
        record = {
            "group_id": group_id,
            "name": name,
            "member_project_ids": members,
            "version": version,
        }
        digest = _sha256(record)
        revision_id = str(uuid4())
        created_at = _utc_now()

        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """
                INSERT INTO workspace_registry_group_revisions(
                    revision_id,group_id,version,owner_id,created_at,
                    previous_revision_id,record_json,record_sha256
                ) VALUES(?,?,?,?,?,?,?,?)
                """,
                (
                    revision_id,
                    group_id,
                    version,
                    owner_id,
                    created_at,
                    previous_revision_id,
                    _canonical_json(record),
                    digest,
                ),
            )
            conn.execute(
                """
                INSERT INTO workspace_registry_groups(
                    group_id,name,member_project_ids_json,version,
                    record_sha256,revision_id
                ) VALUES(?,?,?,?,?,?)
                ON CONFLICT(group_id) DO UPDATE SET
                    name=excluded.name,
                    member_project_ids_json=excluded.member_project_ids_json,
                    version=excluded.version,
                    record_sha256=excluded.record_sha256,
                    revision_id=excluded.revision_id
                """,
                (
                    group_id,
                    name,
                    _canonical_json(members),
                    version,
                    digest,
                    revision_id,
                ),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        return self.get_group(group_id)

    def get_group(self, group_id: str) -> RegistryGroup:
        row = self.store.connect().execute(
            "SELECT * FROM workspace_registry_groups WHERE group_id=?",
            (group_id,),
        ).fetchone()
        if row is None:
            raise RegistryDenied(
                "unknown_project_group",
                "Registered project group does not exist.",
            )
        members = list(json.loads(row["member_project_ids_json"]))
        material = {
            "group_id": row["group_id"],
            "name": row["name"],
            "member_project_ids": members,
            "version": int(row["version"]),
        }
        digest = _sha256(material)
        if digest != row["record_sha256"]:
            raise RegistryDenied(
                "registry_integrity_failure",
                "Current project-group checksum does not match its contents.",
            )
        revision = self.store.connect().execute(
            """
            SELECT record_json,record_sha256 FROM workspace_registry_group_revisions
            WHERE revision_id=? AND group_id=? AND version=?
            """,
            (row["revision_id"], row["group_id"], int(row["version"])),
        ).fetchone()
        if revision is None:
            raise RegistryDenied(
                "registry_integrity_failure",
                "Current project-group revision is missing.",
            )
        if (
            revision["record_sha256"] != digest
            or json.loads(revision["record_json"]) != material
        ):
            raise RegistryDenied(
                "registry_integrity_failure",
                "Current project-group row disagrees with its immutable revision.",
            )
        return RegistryGroup(
            group_id=row["group_id"],
            name=row["name"],
            member_project_ids=tuple(members),
            version=int(row["version"]),
            record_sha256=row["record_sha256"],
            revision_id=row["revision_id"],
        )

    def resolve_scope(
        self,
        scope_token: str,
        *,
        active_project_id: str | None = None,
        max_projects: int = 8,
    ) -> ScopeResolution:
        token = _required(scope_token, "scope_token")
        if max_projects < 1 or max_projects > 50:
            raise RegistryDenied(
                "invalid_scope_cap",
                "max_projects must be between 1 and 50.",
            )

        if token == "active_project":
            if not active_project_id:
                raise RegistryDenied(
                    "missing_active_project",
                    "active_project scope requires active_project_id.",
                )
            candidate_ids = [active_project_id]
        elif token == "registered_projects":
            rows = self.store.connect().execute(
                """
                SELECT project_id FROM workspace_registry_projects
                WHERE trust_class IN (?,?)
                  AND archive_state=?
                  AND read_policy=?
                ORDER BY project_id
                """,
                (
                    TrustClass.OWNER_PROJECT.value,
                    TrustClass.SHARED_OR_CLIENT.value,
                    ArchiveState.ACTIVE.value,
                    ReadPolicy.ALLOWED.value,
                ),
            ).fetchall()
            candidate_ids = [str(row["project_id"]) for row in rows]
        elif token == "donor_repos":
            rows = self.store.connect().execute(
                """
                SELECT project_id FROM workspace_registry_projects
                WHERE trust_class=?
                  AND archive_state=?
                  AND read_policy=?
                ORDER BY project_id
                """,
                (
                    TrustClass.DONOR_REPO.value,
                    ArchiveState.ACTIVE.value,
                    ReadPolicy.ALLOWED.value,
                ),
            ).fetchall()
            candidate_ids = [str(row["project_id"]) for row in rows]
        elif token == "archived_projects":
            rows = self.store.connect().execute(
                """
                SELECT project_id FROM workspace_registry_projects
                WHERE archive_state=? AND read_policy=?
                ORDER BY project_id
                """,
                (ArchiveState.ARCHIVED.value, ReadPolicy.ALLOWED.value),
            ).fetchall()
            candidate_ids = [str(row["project_id"]) for row in rows]
        elif token.startswith("project_group:"):
            group = self.get_group(token.split(":", 1)[1])
            candidate_ids = list(group.member_project_ids)
        elif token.startswith("project:"):
            candidate_ids = [token.split(":", 1)[1]]
        else:
            raise RegistryDenied(
                "unknown_semantic_scope",
                "Semantic project scope is not registered.",
            )

        if not candidate_ids:
            raise RegistryDenied("empty_scope", "Resolved project scope is empty.")
        if len(candidate_ids) > max_projects:
            raise RegistryDenied(
                "scope_project_cap_exceeded",
                "Resolved scope exceeds ORION project-count cap.",
            )

        projects: list[ResolvedProject] = []
        roots: dict[str, str] = {}
        for project_id in candidate_ids:
            item = self.get_project(project_id)
            if item.read_policy != ReadPolicy.ALLOWED:
                raise RegistryDenied(
                    "project_read_blocked",
                    "Resolved scope contains a project not authorized for read.",
                )
            if (
                token != "archived_projects"
                and item.archive_state == ArchiveState.ARCHIVED
            ):
                raise RegistryDenied(
                    "archived_project_not_explicit",
                    "Archived project requires explicit archived scope.",
                )
            projects.append(
                ResolvedProject(
                    project_id=item.project_id,
                    name=item.name,
                    repo_identity=item.repo_identity,
                    trust_class=item.trust_class.value,
                    archive_state=item.archive_state.value,
                    no_cloud=item.no_cloud,
                    license_state=item.license_state,
                    revision=item.revision,
                    registry_version=item.version,
                    registry_sha256=item.record_sha256,
                )
            )
            roots[item.project_id] = item.trusted_root

        resolution_material = {
            "scope_token": token,
            "projects": [
                {
                    "project_id": item.project_id,
                    "registry_version": item.registry_version,
                    "registry_sha256": item.registry_sha256,
                }
                for item in projects
            ],
        }
        return ScopeResolution(
            scope_token=token,
            resolution_id=_sha256(resolution_material),
            resolved_at=_utc_now(),
            projects=tuple(projects),
            trusted_roots=roots,
        )


__all__ = [
    "ArchiveState",
    "ReadPolicy",
    "RegistryDenied",
    "RegistryGroup",
    "RegistryProject",
    "ResolvedProject",
    "ScopeResolution",
    "TrustClass",
    "WorkspaceRegistry",
    "WritePolicy",
]
