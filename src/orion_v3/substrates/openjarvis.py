from __future__ import annotations

import json
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Callable, Iterator, Mapping

from orion_v3.authority import AuthorityDenied, AuthorityGateway, AuthorizedOperation


_ACTIVE_ACTION_LEASE: ContextVar[str | None] = ContextVar(
    "orion_active_action_lease", default=None
)


@contextmanager
def bind_action_lease(token: str) -> Iterator[None]:
    """Bind an ORION lease out-of-band from model/tool arguments."""

    marker = _ACTIVE_ACTION_LEASE.set(token)
    try:
        yield
    finally:
        _ACTIVE_ACTION_LEASE.reset(marker)


def build_gate1_capability_policy(agent_id: str):
    """Create the only acceptable OpenJarvis capability posture for Gate 1."""

    from openjarvis.security.capabilities import CapabilityPolicy

    policy = CapabilityPolicy(default_deny=True)
    policy.grant(agent_id, "file:read", "orion_filesystem_search")
    return policy


def build_filesystem_search_tool(
    gateway: AuthorityGateway,
    dispatcher: Callable[[AuthorizedOperation], Mapping[str, Any]],
):
    """Build a Jarvis tool that has zero authority of its own.

    The model sees search parameters only. The lease is supplied through an
    ORION-owned execution context and every call crosses AuthorityGateway.
    """

    from openjarvis.core.types import ToolResult
    from openjarvis.tools._stubs import BaseTool, ToolSpec

    class OrionFilesystemSearchTool(BaseTool):
        tool_id = "orion_filesystem_search"
        is_local = True

        @property
        def spec(self) -> ToolSpec:
            return ToolSpec(
                name=self.tool_id,
                description=(
                    "Search exact filenames inside ORION-authorized local locations. "
                    "ORION supplies trust roots and authority out of band."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "exact_names": {"type": "array", "items": {"type": "string"}},
                        "locations": {"type": "array", "items": {"type": "string"}},
                        "recursive": {"type": "boolean"},
                        "max_depth": {"type": "integer"},
                        "max_results": {"type": "integer"},
                    },
                    "required": ["exact_names", "locations"],
                    "additionalProperties": False,
                },
                category="orion",
                required_capabilities=["file:read"],
            )

        def execute(self, **params: Any) -> ToolResult:
            try:
                authorized = gateway.authorize(
                    lease_token=_ACTIVE_ACTION_LEASE.get(),
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

            try:
                result = dict(dispatcher(authorized))
            except Exception as exc:
                return ToolResult(
                    tool_name=self.tool_id,
                    content="ORION Hand execution failed.",
                    success=False,
                    metadata={
                        "orion_lease_id": authorized.lease.lease_id,
                        "orion_error_type": type(exc).__name__,
                    },
                )

            return ToolResult(
                tool_name=self.tool_id,
                content=json.dumps(result, ensure_ascii=False, sort_keys=True),
                success=True,
                metadata={
                    "orion_lease_id": authorized.lease.lease_id,
                    "orion_operation_id": authorized.operation_id,
                    "orion_result": result,
                },
            )

    return OrionFilesystemSearchTool()