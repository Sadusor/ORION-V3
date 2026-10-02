from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .leases import ActionLease, LeaseAuthority, LeaseDenied


class AuthorityDenied(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class AuthorizedOperation:
    operation_id: str
    arguments: Mapping[str, Any]
    lease: ActionLease


_FILESYSTEM_SEARCH_ARGS = frozenset(
    {
        "exact_names",
        "locations",
        "recursive",
        "max_depth",
        "max_results",
        "reveal_containing_folders",
    }
)

_TRUST_ANCHOR_NAMES = frozenset(
    {
        "roots",
        "local_roots",
        "repo_root",
        "expected_repo",
        "expected_branch",
        "credential",
        "credentials",
        "opener",
        "launcher",
    }
)


def _deny(code: str, message: str) -> None:
    raise AuthorityDenied(code, message)


def _bounded_int(value: Any, *, field: str, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        _deny("invalid_argument", f"{field} must be an integer")
    if number < minimum or number > maximum:
        _deny("scope_violation", f"{field} exceeds the authorized bound")
    return number


def _authorize_filesystem_search(
    arguments: Mapping[str, Any],
    lease: ActionLease,
) -> dict[str, Any]:
    if not isinstance(arguments, Mapping):
        _deny("invalid_arguments", "filesystem.search arguments must be an object")

    keys = set(arguments)
    if keys & _TRUST_ANCHOR_NAMES:
        _deny(
            "trusted_binding_override",
            "Model/tool arguments may not provide ORION trust anchors.",
        )
    unknown = keys - _FILESYSTEM_SEARCH_ARGS
    if unknown:
        _deny("unknown_argument", "Unsupported filesystem.search argument: " + sorted(unknown)[0])

    names = arguments.get("exact_names")
    if not isinstance(names, list) or not names:
        _deny("invalid_argument", "exact_names must be a non-empty array")
    clean_names: list[str] = []
    for raw in names:
        name = str(raw or "").strip()
        if not name or "/" in name or "\\" in name or name in {".", ".."}:
            _deny("invalid_argument", "exact_names must contain safe basenames only")
        clean_names.append(name)
    if len(clean_names) > 20:
        _deny("scope_violation", "exact_names exceeds the Gate-1 bound")

    requested_locations = arguments.get("locations")
    if not isinstance(requested_locations, list) or not requested_locations:
        _deny("invalid_argument", "locations must be a non-empty array")
    requested_locations = [str(x).strip().lower() for x in requested_locations if str(x).strip()]
    allowed_locations = {str(x).strip().lower() for x in lease.scope.get("locations", [])}
    if not requested_locations or not set(requested_locations).issubset(allowed_locations):
        _deny("scope_violation", "Requested filesystem location is outside the Action Lease")

    allow_recursive = bool(lease.scope.get("recursive", False))
    recursive = bool(arguments.get("recursive", allow_recursive))
    if recursive and not allow_recursive:
        _deny("scope_violation", "Recursive search is not authorized by the Action Lease")

    allowed_depth = _bounded_int(
        lease.scope.get("max_depth", 0), field="lease.max_depth", minimum=0, maximum=6
    )
    max_depth = _bounded_int(
        arguments.get("max_depth", min(4, allowed_depth)),
        field="max_depth",
        minimum=0,
        maximum=allowed_depth,
    )

    allowed_results = _bounded_int(
        lease.scope.get("max_results", 1), field="lease.max_results", minimum=1, maximum=50
    )
    max_results = _bounded_int(
        arguments.get("max_results", min(50, allowed_results)),
        field="max_results",
        minimum=1,
        maximum=allowed_results,
    )

    if bool(arguments.get("reveal_containing_folders", False)):
        _deny(
            "operation_widening",
            "filesystem.search may not widen itself into filesystem.reveal.",
        )

    return {
        "exact_names": clean_names,
        "locations": requested_locations,
        "recursive": recursive,
        "max_depth": max_depth,
        "max_results": max_results,
        "reveal_containing_folders": False,
    }


class AuthorityGateway:
    """Single Gate-1 authorization point before any substrate Hand dispatch."""

    def __init__(self, leases: LeaseAuthority) -> None:
        self._leases = leases

    def authorize(
        self,
        *,
        lease_token: str | None,
        operation_id: str,
        arguments: Mapping[str, Any],
    ) -> AuthorizedOperation:
        try:
            lease = self._leases.validate(lease_token, operation_id=operation_id)
        except LeaseDenied as exc:
            raise AuthorityDenied(exc.code, str(exc)) from exc

        if operation_id != "filesystem.search":
            _deny("unsupported_operation", "Gate 1 authorizes filesystem.search only")

        sanitized = _authorize_filesystem_search(arguments, lease)
        return AuthorizedOperation(
            operation_id=operation_id,
            arguments=sanitized,
            lease=lease,
        )