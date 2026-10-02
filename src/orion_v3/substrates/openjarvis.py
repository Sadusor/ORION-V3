from __future__ import annotations

import json
from typing import Any, Callable, Mapping

from orion_v3.authority import AuthorityDenied, AuthorityGateway, AuthorizedOperation


def build_gate1_capability_policy(agent_id: str):
    """Create the only acceptable OpenJarvis capability posture for Gate 1."""

    from openjarvis.security.capabilities import CapabilityPolicy

    policy = CapabilityPolicy(default_deny=True)
    policy.grant(agent_id, "file:read", "orion_filesystem_search")
    return policy


def build_filesystem_search_tool(
    gateway: AuthorityGateway,
    dispatcher: Callable[[AuthorizedOperation], Mapping[str, Any]],
    *,
    lease_token: str | None = None,
):
    """Build one OpenJarvis proxy tool instance.

    The lease is captured privately on the tool instance, never exposed in the
    model-facing ToolSpec or argument schema. An unbound instance is useful as
    a deliberate bypass probe: it remains discoverable/invokable by Jarvis but
    must fail at the ORION Gateway before dispatcher invocation.

    A bound instance is ephemeral authority: ORION creates it only after
    issuing a lease for the current dispatch. This avoids thread-local/context
    propagation assumptions inside donor executors.
    """

    from openjarvis.core.types import ToolResult
    from openjarvis.tools._stubs import BaseTool, ToolSpec

    class OrionFilesystemSearchTool(BaseTool):
        tool_id = "orion_filesystem_search"
        is_local = True

        def __init__(self, token: str | None) -> None:
            self._orion_lease_token = token

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
                    lease_token=self._orion_lease_token,
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

    return OrionFilesystemSearchTool(lease_token)
