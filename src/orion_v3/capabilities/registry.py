from __future__ import annotations

from typing import Mapping

from .model import (
    ApprovalClass,
    CapabilityContractError,
    CapabilityDefinition,
    CapabilityProposal,
    CapabilityStatus,
    EffectClass,
    ParameterSpec,
    ResolvedCapability,
)


_LOCAL_ROOTS = (
    "desktop",
    "downloads",
    "documents",
    "active_project",
    "orion_artifacts",
)


class CapabilityRegistry:
    """ORION semantic/policy registry.

    This is deliberately not a low-level tool registry. Concrete execution
    remains in donor/native implementations selected by deterministic ORION
    policy.
    """

    def __init__(self, definitions: Mapping[str, CapabilityDefinition]) -> None:
        self._definitions = dict(definitions)

    def get(self, capability_id: str) -> CapabilityDefinition:
        try:
            return self._definitions[capability_id]
        except KeyError as exc:
            raise CapabilityContractError(
                f"Unknown ORION capability: {capability_id or '(empty)'}"
            ) from exc

    def resolve(self, proposal: CapabilityProposal) -> ResolvedCapability:
        if proposal.ambiguity is not None:
            raise CapabilityContractError(
                "Ambiguous proposal cannot resolve to a capability"
            )
        if proposal.intent is None:
            raise CapabilityContractError("Capability intent is required")
        definition = self.get(proposal.intent)
        if definition.status in {
            CapabilityStatus.RETIRED,
            CapabilityStatus.BLOCKED,
        }:
            raise CapabilityContractError(
                f"Capability is not dispatchable: {definition.capability_id}"
            )
        return ResolvedCapability(
            definition=definition,
            params=definition.normalize_params(proposal.params),
        )

    def snapshot(self) -> dict[str, CapabilityDefinition]:
        return dict(self._definitions)


def _legacy_evidence(path: str) -> tuple[str, ...]:
    return (path,)


def inherited_registry_v0() -> CapabilityRegistry:
    """First V3 semantic records harvested from physically proven legacy work."""

    definitions = {
        "project.publish_exact_artifact": CapabilityDefinition(
            capability_id="project.publish_exact_artifact",
            version=0,
            purpose=(
                "Publish exactly one authorized UTF-8 repository artifact and "
                "prove the remote branch tip equals the resulting local commit."
            ),
            status=CapabilityStatus.PROVEN_ACTIVE,
            parameters={
                "artifact_path": ParameterSpec("string", max_length=1024),
                "artifact_content": ParameterSpec(
                    "string", max_length=2_000_000, strip_whitespace=False
                ),
            },
            effect_class=EffectClass.BOUNDED_MODIFICATION,
            approval_class=ApprovalClass.BOUNDED_MODIFICATION,
            allowed_scopes=("active_project",),
            binding_requirements=(
                "ready_project_link_or_equivalent_trusted_repo_binding",
                "exact_repo_branch_identity",
            ),
            implementation_candidates=(
                "legacy_orion.publish_exact_artifact",
            ),
            active_implementation="legacy_orion.publish_exact_artifact",
            availability_probe="trusted project binding is READY",
            preconditions=(
                "repo root exact",
                "named branch exact",
                "origin identity exact",
                "local HEAD equals remote before publish",
                "no pre-existing staged paths",
                "artifact path stays inside authorized scope",
            ),
            stop_contract=(
                "Git subprocesses are bounded; no force/reset/arbitrary checkout; "
                "a completed remote push is not rolled back automatically."
            ),
            evidence_contract=(
                "artifact_sha256",
                "local_head",
                "remote_head",
                "origin_repo",
                "branch",
                "proof",
            ),
            postconditions=(
                "authorized artifact hash matches",
                "remote_head equals local_head",
                "no unrelated staged path escaped scope",
            ),
            provenance="legacy ORION Remote Capability Registry V0",
            validated_sha="2a78f8015b0a6b0552320ee4b535624bfd7fc13b",
            physical_evidence_refs=_legacy_evidence(
                "Sadusor/Orion:docs/decisions/0014-capability-registry-deterministic-hands.md"
            ),
        ),
        "browser.open_url": CapabilityDefinition(
            capability_id="browser.open_url",
            version=1,
            purpose="Launch one validated HTTP/HTTPS URL in a visible browser.",
            status=CapabilityStatus.PROVEN_ACTIVE,
            parameters={
                "url": ParameterSpec("string", max_length=4096),
                "browser": ParameterSpec(
                    "string",
                    required=False,
                    default="default",
                    enum=("default", "chrome"),
                ),
            },
            effect_class=EffectClass.REVERSIBLE_ROUTINE,
            approval_class=ApprovalClass.REVERSIBLE_ROUTINE,
            allowed_scopes=("pc/browser",),
            binding_requirements=("approved_browser_launcher",),
            implementation_candidates=("legacy_orion.open_web_url",),
            active_implementation="legacy_orion.open_web_url",
            availability_probe="requested browser launcher is available",
            preconditions=(
                "URL scheme is http/https",
                "URL has hostname",
                "URL has no embedded credentials",
            ),
            stop_contract=(
                "Capability owns only its launch request; it must not kill a "
                "pre-existing user browser session."
            ),
            evidence_contract=(
                "launcher",
                "url",
                "host",
                "proof",
            ),
            postconditions=(
                "OS accepted launch request",
                "do not claim page content was read unless separately verified",
            ),
            provenance="legacy ORION Remote Capability Registry V1",
            validated_sha="4d339416bf4953ce2d19907312a69bdcce715dc1",
            physical_evidence_refs=_legacy_evidence(
                "Sadusor/Orion:docs/checkpoints/2026-10-02-capability-registry-v1-open-web-url-staged.md"
            ),
        ),
        "fs.search_exact": CapabilityDefinition(
            capability_id="fs.search_exact",
            version=2,
            purpose=(
                "Search exact basenames inside deterministic named local roots "
                "without reading file contents."
            ),
            status=CapabilityStatus.PROVEN_ACTIVE,
            parameters={
                "exact_names": ParameterSpec(
                    "string_list",
                    min_items=1,
                    max_items=20,
                    max_length=255,
                ),
                "locations": ParameterSpec(
                    "string_list",
                    min_items=1,
                    max_items=len(_LOCAL_ROOTS),
                    enum=_LOCAL_ROOTS,
                ),
                "recursive": ParameterSpec("bool", required=False, default=True),
                "max_depth": ParameterSpec(
                    "int",
                    required=False,
                    default=4,
                    min_value=0,
                    max_value=6,
                ),
                "max_results": ParameterSpec(
                    "int",
                    required=False,
                    default=50,
                    min_value=1,
                    max_value=50,
                ),
                "reveal_containing_folders": ParameterSpec(
                    "bool",
                    required=False,
                    default=False,
                ),
            },
            effect_class=EffectClass.READ_ONLY,
            approval_class=ApprovalClass.READ_ONLY,
            allowed_scopes=_LOCAL_ROOTS,
            binding_requirements=("named_local_roots",),
            implementation_candidates=("legacy_orion.find_local_files",),
            active_implementation="legacy_orion.find_local_files",
            availability_probe="at least one requested named root exists",
            preconditions=(
                "exact basenames only",
                "bounded depth/results",
                "symlink/junction descent disabled",
            ),
            stop_contract="Bounded synchronous scan; cancellation may stop the owned worker.",
            evidence_contract=(
                "searched_locations",
                "unavailable_locations",
                "found",
                "not_found_names",
                "truncated",
                "proof",
            ),
            postconditions=(
                "result paths remain under requested trusted roots",
                "negative result is scoped to searched locations only",
            ),
            provenance="legacy ORION Remote Local File Hand V2",
            validated_sha="575d9e334524358bf7ac0be131503a991a43eef1",
            physical_evidence_refs=_legacy_evidence(
                "Sadusor/Orion:docs/checkpoints/2026-10-02-local-file-hand-v2-physical-pass.md"
            ),
        ),
        "fs.reveal": CapabilityDefinition(
            capability_id="fs.reveal",
            version=2,
            purpose="Open Windows Explorer at a validated directory under a named root.",
            status=CapabilityStatus.PROVEN_ACTIVE,
            parameters={
                "location": ParameterSpec("string", enum=_LOCAL_ROOTS),
                "relative_path": ParameterSpec(
                    "string",
                    required=False,
                    default=".",
                    max_length=2048,
                ),
            },
            effect_class=EffectClass.REVERSIBLE_ROUTINE,
            approval_class=ApprovalClass.REVERSIBLE_ROUTINE,
            allowed_scopes=_LOCAL_ROOTS,
            binding_requirements=("named_local_roots",),
            implementation_candidates=("legacy_orion.reveal_in_explorer",),
            active_implementation="legacy_orion.reveal_in_explorer",
            availability_probe="target named root exists",
            preconditions=(
                "relative path only",
                "target resolves inside named root",
                "target exists and is a directory",
            ),
            stop_contract=(
                "Explorer launch is routine/reversible; capability does not own "
                "unrelated existing Explorer windows."
            ),
            evidence_contract=("location", "relative_path", "path", "proof"),
            postconditions=("validated target stayed inside trusted root",),
            provenance="legacy ORION Remote Local File Hand V2",
            validated_sha="575d9e334524358bf7ac0be131503a991a43eef1",
            physical_evidence_refs=_legacy_evidence(
                "Sadusor/Orion:docs/checkpoints/2026-10-02-local-file-hand-v2-physical-pass.md"
            ),
        ),
        "fs.list": CapabilityDefinition(
            capability_id="fs.list",
            version=3,
            purpose=(
                "Enumerate bounded file/folder metadata inside deterministic "
                "named local roots."
            ),
            status=CapabilityStatus.EXPERIMENTAL,
            parameters={
                "locations": ParameterSpec(
                    "string_list",
                    min_items=1,
                    max_items=len(_LOCAL_ROOTS),
                    enum=_LOCAL_ROOTS,
                ),
                "item_kind": ParameterSpec(
                    "string",
                    required=False,
                    default="both",
                    enum=("files", "folders", "both"),
                ),
                "sort": ParameterSpec(
                    "string",
                    required=False,
                    default="oldest_modified",
                    enum=("oldest_modified", "newest_modified"),
                ),
                "recursive": ParameterSpec("bool", required=False, default=True),
                "max_depth": ParameterSpec(
                    "int",
                    required=False,
                    default=4,
                    min_value=0,
                    max_value=6,
                ),
                "max_results": ParameterSpec(
                    "int",
                    required=False,
                    default=50,
                    min_value=1,
                    max_value=100,
                ),
            },
            effect_class=EffectClass.READ_ONLY,
            approval_class=ApprovalClass.READ_ONLY,
            allowed_scopes=_LOCAL_ROOTS,
            binding_requirements=("named_local_roots",),
            implementation_candidates=("legacy_orion.list_local_items",),
            active_implementation="legacy_orion.list_local_items",
            availability_probe="at least one requested named root exists",
            preconditions=(
                "bounded depth/results/scan budget",
                "symlink/junction descent disabled",
            ),
            stop_contract="Bounded synchronous scan; cancellation may stop the owned worker.",
            evidence_contract=(
                "searched_locations",
                "items",
                "result_truncated",
                "scan_truncated",
                "proof",
            ),
            postconditions=(
                "metadata only",
                "modified time never presented as proof of last use",
            ),
            provenance="legacy ORION Remote Capability Registry V3 source/probe",
            validated_sha=None,
            physical_evidence_refs=(),
        ),
    }
    return CapabilityRegistry(definitions)
