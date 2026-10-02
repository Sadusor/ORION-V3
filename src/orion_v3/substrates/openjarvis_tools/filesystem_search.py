from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from openjarvis.core.registry import ToolRegistry
from openjarvis.core.types import ToolResult
from openjarvis.tools._stubs import BaseTool, ToolSpec

from orion_v3.authority import AuthorityDenied, AuthorityGateway


_IMPLEMENTATION_ID = "openjarvis.tool.orion_filesystem_search.v1"


@ToolRegistry.register("orion_filesystem_search")
class OrionFilesystemSearchTool(BaseTool):
    """OpenJarvis-native exact-basename search under ORION authority.

    OpenJarvis owns the tool interface, registration and execution plumbing.
    ORION injects the Action Lease and trusted root bindings out of band.
    """

    tool_id = "orion_filesystem_search"
    is_local = True

    def __init__(
        self,
        *,
        gateway: AuthorityGateway,
        lease_token: str | None,
        trusted_roots: Mapping[str, str | Path],
    ) -> None:
        self._gateway = gateway
        self._lease_token = lease_token
        roots: dict[str, Path] = {}
        for raw_name, raw_path in trusted_roots.items():
            name = str(raw_name).strip().lower()
            if not name:
                raise ValueError("trusted root name must not be empty")
            path = Path(raw_path).expanduser().resolve()
            if not path.exists() or not path.is_dir():
                raise ValueError(
                    f"trusted root '{name}' is not an existing directory"
                )
            roots[name] = path
        self._trusted_roots = roots

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self.tool_id,
            description=(
                "Search exact basenames inside ORION-authorized logical locations. "
                "Absolute trusted roots are never model arguments."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "exact_names": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "locations": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "recursive": {"type": "boolean"},
                    "max_depth": {"type": "integer"},
                    "max_results": {"type": "integer"},
                },
                "required": ["exact_names", "locations"],
                "additionalProperties": False,
            },
            category="filesystem",
            required_capabilities=["file:read"],
            timeout_seconds=10.0,
        )

    @staticmethod
    def _key(value: str) -> str:
        return os.path.normcase(value)

    @staticmethod
    def _metadata(root: Path, entry: Path, location: str) -> dict[str, Any]:
        stat = entry.stat(follow_symlinks=False)
        if entry.is_symlink():
            kind = "symlink"
        elif entry.is_dir():
            kind = "directory"
        elif entry.is_file():
            kind = "file"
        else:
            kind = "other"
        return {
            "location": location,
            "relative_path": entry.relative_to(root).as_posix(),
            "name": entry.name,
            "kind": kind,
            "size_bytes": stat.st_size if kind == "file" else None,
            "modified_ns": stat.st_mtime_ns,
        }

    def _search_location(
        self,
        *,
        location: str,
        names: set[str],
        recursive: bool,
        max_depth: int,
        remaining: int,
    ) -> list[dict[str, Any]]:
        try:
            root = self._trusted_roots[location]
        except KeyError as exc:
            raise RuntimeError(
                f"ORION trusted root binding missing for '{location}'"
            ) from exc

        matches: list[dict[str, Any]] = []

        if not recursive:
            entries = sorted(root.iterdir(), key=lambda p: self._key(p.name))
            for entry in entries:
                if self._key(entry.name) in names:
                    matches.append(self._metadata(root, entry, location))
                    if len(matches) >= remaining:
                        break
            return matches

        for current_raw, dirnames, filenames in os.walk(
            root,
            topdown=True,
            followlinks=False,
        ):
            current = Path(current_raw)
            relative_dir = current.relative_to(root)
            depth = 0 if relative_dir == Path(".") else len(relative_dir.parts)

            # Never descend through symlinked directories.
            dirnames[:] = sorted(
                [
                    name
                    for name in dirnames
                    if not (current / name).is_symlink()
                ],
                key=self._key,
            )
            filenames.sort(key=self._key)

            for name in sorted([*dirnames, *filenames], key=self._key):
                if self._key(name) not in names:
                    continue
                matches.append(self._metadata(root, current / name, location))
                if len(matches) >= remaining:
                    return matches

            if depth >= max_depth:
                dirnames[:] = []

        return matches

    def execute(self, **params: Any) -> ToolResult:
        try:
            authorized = self._gateway.authorize(
                lease_token=self._lease_token,
                operation_id="filesystem.search",
                arguments=params,
            )
        except AuthorityDenied as exc:
            return ToolResult(
                tool_name=self.tool_id,
                content="ORION authority denied filesystem.search.",
                success=False,
                metadata={"orion_denial_code": exc.code},
            )

        args = authorized.arguments
        wanted = {self._key(name) for name in args["exact_names"]}
        max_results = int(args["max_results"])

        matches: list[dict[str, Any]] = []
        try:
            for location in args["locations"]:
                remaining = max_results - len(matches)
                if remaining <= 0:
                    break
                matches.extend(
                    self._search_location(
                        location=location,
                        names=wanted,
                        recursive=bool(args["recursive"]),
                        max_depth=int(args["max_depth"]),
                        remaining=remaining,
                    )
                )
        except (OSError, RuntimeError, ValueError) as exc:
            return ToolResult(
                tool_name=self.tool_id,
                content="OpenJarvis filesystem search execution failed.",
                success=False,
                metadata={
                    "orion_lease_id": authorized.lease.lease_id,
                    "orion_operation_id": authorized.operation_id,
                    "orion_error_type": type(exc).__name__,
                },
            )

        result = {
            "operation_id": authorized.operation_id,
            "implementation_id": _IMPLEMENTATION_ID,
            "searched_locations": list(args["locations"]),
            "matches": matches,
            "match_count": len(matches),
            "truncated": len(matches) >= max_results,
        }

        return ToolResult(
            tool_name=self.tool_id,
            content=json.dumps(result, ensure_ascii=False, sort_keys=True),
            success=True,
            metadata={
                "orion_lease_id": authorized.lease.lease_id,
                "orion_operation_id": authorized.operation_id,
                "orion_implementation_id": _IMPLEMENTATION_ID,
                "orion_result": result,
            },
        )


__all__ = ["OrionFilesystemSearchTool"]
