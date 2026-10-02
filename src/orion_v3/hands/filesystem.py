from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from orion_v3.authority import AuthorizedOperation
from orion_v3.evidence import EvidenceEnvelope, Outcome


class FilesystemHandError(RuntimeError):
    pass


@dataclass(frozen=True)
class TrustedFilesystemRoots:
    """ORION-owned filesystem trust bindings.

    Location names may be model-visible; absolute roots are not.
    """

    roots: Mapping[str, Path]

    def __post_init__(self) -> None:
        normalized: dict[str, Path] = {}
        for raw_name, raw_path in self.roots.items():
            name = str(raw_name).strip().lower()
            if not name:
                raise ValueError("trusted root name must not be empty")
            path = Path(raw_path).expanduser().resolve()
            if not path.exists() or not path.is_dir():
                raise ValueError(f"trusted root '{name}' is not an existing directory")
            normalized[name] = path
        object.__setattr__(self, "roots", normalized)

    def resolve(self, location: str) -> Path:
        key = str(location).strip().lower()
        try:
            return self.roots[key]
        except KeyError as exc:
            raise FilesystemHandError(
                f"ORION has no trusted filesystem binding for location '{key}'"
            ) from exc


class FilesystemSearchHand:
    """Deterministic exact-basename search with no shell fallback."""

    implementation_id = "orion.filesystem.search.v1"

    def __init__(self, trusted_roots: TrustedFilesystemRoots) -> None:
        self._trusted_roots = trusted_roots

    @staticmethod
    def _name_key(value: str) -> str:
        return os.path.normcase(value)

    @staticmethod
    def _entry_metadata(root: Path, entry: Path, location: str) -> dict[str, Any]:
        try:
            stat = entry.stat(follow_symlinks=False)
        except OSError as exc:
            raise FilesystemHandError(
                f"metadata read failed for a result under '{location}': "
                f"{type(exc).__name__}"
            ) from exc

        if entry.is_symlink():
            kind = "symlink"
        elif entry.is_dir():
            kind = "directory"
        elif entry.is_file():
            kind = "file"
        else:
            kind = "other"

        relative = entry.relative_to(root).as_posix()
        return {
            "location": location,
            "relative_path": relative,
            "name": entry.name,
            "kind": kind,
            "size_bytes": stat.st_size if kind == "file" else None,
            "modified_ns": stat.st_mtime_ns,
        }

    def execute(self, authorized: AuthorizedOperation) -> Mapping[str, Any]:
        if authorized.operation_id != "filesystem.search":
            raise FilesystemHandError(
                f"unsupported operation for FilesystemSearchHand: "
                f"{authorized.operation_id}"
            )

        args = authorized.arguments
        wanted = {self._name_key(name) for name in args["exact_names"]}
        recursive = bool(args["recursive"])
        max_depth = int(args["max_depth"])
        max_results = int(args["max_results"])

        matches: list[dict[str, Any]] = []
        truncated = False

        for location in args["locations"]:
            root = self._trusted_roots.resolve(location)

            if not recursive:
                try:
                    entries = sorted(root.iterdir(), key=lambda p: self._name_key(p.name))
                except OSError as exc:
                    raise FilesystemHandError(
                        f"directory enumeration failed for '{location}': "
                        f"{type(exc).__name__}"
                    ) from exc

                for entry in entries:
                    if self._name_key(entry.name) not in wanted:
                        continue
                    matches.append(self._entry_metadata(root, entry, location))
                    if len(matches) >= max_results:
                        truncated = True
                        break
            else:
                try:
                    walker = os.walk(root, topdown=True, followlinks=False)
                    for current_raw, dirnames, filenames in walker:
                        current = Path(current_raw)
                        try:
                            relative_dir = current.relative_to(root)
                        except ValueError as exc:
                            raise FilesystemHandError(
                                "filesystem traversal escaped its ORION trusted root"
                            ) from exc

                        depth = 0 if relative_dir == Path(".") else len(relative_dir.parts)
                        dirnames[:] = sorted(
                            [
                                name
                                for name in dirnames
                                if not (current / name).is_symlink()
                            ],
                            key=self._name_key,
                        )
                        filenames.sort(key=self._name_key)

                        candidate_names = sorted(
                            list(dirnames) + list(filenames),
                            key=self._name_key,
                        )
                        for name in candidate_names:
                            if self._name_key(name) not in wanted:
                                continue
                            matches.append(
                                self._entry_metadata(root, current / name, location)
                            )
                            if len(matches) >= max_results:
                                truncated = True
                                break

                        if len(matches) >= max_results:
                            break
                        if depth >= max_depth:
                            dirnames[:] = []
                except OSError as exc:
                    raise FilesystemHandError(
                        f"recursive enumeration failed for '{location}': "
                        f"{type(exc).__name__}"
                    ) from exc

            if len(matches) >= max_results:
                break

        return {
            "operation_id": "filesystem.search",
            "implementation_id": self.implementation_id,
            "searched_locations": list(args["locations"]),
            "matches": matches,
            "match_count": len(matches),
            "truncated": truncated,
        }


def normalize_search_evidence(
    authorized: AuthorizedOperation,
    result: Mapping[str, Any],
) -> EvidenceEnvelope:
    """Convert deterministic Hand output into ORION canonical evidence."""

    if authorized.operation_id != "filesystem.search":
        raise FilesystemHandError("cannot normalize evidence for another operation")
    if result.get("operation_id") != "filesystem.search":
        raise FilesystemHandError("filesystem.search result operation mismatch")
    if result.get("implementation_id") != FilesystemSearchHand.implementation_id:
        raise FilesystemHandError("filesystem.search implementation mismatch")

    return EvidenceEnvelope(
        task_id=authorized.lease.task_id,
        lease_id=authorized.lease.lease_id,
        operation_id=authorized.operation_id,
        implementation_id=FilesystemSearchHand.implementation_id,
        outcome=Outcome.CONFIRMED,
        result=dict(result),
        verifier="orion.filesystem.search.structure.v1",
    )
