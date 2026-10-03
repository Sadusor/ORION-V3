from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from orion_v3.capabilities import (
    CapabilityContractError,
    CapabilityRegistry,
)
from .intent import IntentProposal, SemanticIntent


class ResolutionStatus(str, Enum):
    RESOLVED = "RESOLVED"
    NO_CAPABILITY = "NO_CAPABILITY"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass(frozen=True)
class IntentResolution:
    status: ResolutionStatus
    intent: SemanticIntent | None
    capability_id: str | None
    params: Mapping[str, Any]
    reason: str


_SCOPE_MAP = {
    "desktop": "desktop",
    "downloads": "downloads",
    "documents": "documents",
    "active_project": "active_project",
    "orion_artifacts": "orion_artifacts",
}


class IntentResolver:
    """Deterministic semantic intent -> capability resolver."""

    def __init__(self, registry: CapabilityRegistry) -> None:
        self._registry = registry

    def resolve(self, proposal: IntentProposal) -> IntentResolution:
        if proposal.composition:
            return IntentResolution(
                ResolutionStatus.AMBIGUOUS,
                proposal.intent,
                None,
                {},
                "Multiple actions require workflow/composition handling.",
            )
        if proposal.ambiguities:
            return IntentResolution(
                ResolutionStatus.AMBIGUOUS,
                proposal.intent,
                None,
                {},
                "; ".join(proposal.ambiguities),
            )
        if proposal.intent is None:
            return IntentResolution(
                ResolutionStatus.AMBIGUOUS,
                None,
                None,
                {},
                "No semantic intent was resolved.",
            )

        mapper = {
            SemanticIntent.OPEN_WEB_URL: self._open_web_url,
            SemanticIntent.LOCATE_NAMED_FILES: self._locate_named_files,
            SemanticIntent.REVEAL_DIRECTORY: self._reveal_directory,
            SemanticIntent.LIST_LOCAL_ITEMS: self._list_local_items,
            SemanticIntent.PUBLISH_EXACT_ARTIFACT: self._publish_exact_artifact,
        }.get(proposal.intent)

        if mapper is None:
            return IntentResolution(
                ResolutionStatus.NO_CAPABILITY,
                proposal.intent,
                None,
                {},
                "Semantic intent is understood but no registered capability "
                "currently implements it.",
            )

        capability_id, params = mapper(proposal.entities)
        definition = self._registry.get(capability_id)
        normalized = definition.normalize_params(params)
        return IntentResolution(
            ResolutionStatus.RESOLVED,
            proposal.intent,
            capability_id,
            normalized,
            "Exact deterministic intent rule matched.",
        )

    @staticmethod
    def _scope(entities: Mapping[str, Any]) -> str:
        raw = entities.get("scope")
        if not isinstance(raw, str) or raw not in _SCOPE_MAP:
            raise CapabilityContractError(
                "Intent requires a trusted logical scope name."
            )
        return _SCOPE_MAP[raw]

    @staticmethod
    def _open_web_url(entities: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
        url = entities.get("url")
        if not isinstance(url, str) or not url.strip():
            raise CapabilityContractError("OPEN_WEB_URL requires url")
        params: dict[str, Any] = {"url": url.strip()}
        browser = entities.get("browser")
        if browser is not None:
            if browser not in {"default", "chrome"}:
                raise CapabilityContractError("Unsupported browser entity")
            params["browser"] = browser
        return "browser.open_url", params

    @classmethod
    def _locate_named_files(
        cls, entities: Mapping[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        names = entities.get("names")
        if (
            not isinstance(names, list)
            or not names
            or any(not isinstance(item, str) or not item.strip() for item in names)
        ):
            raise CapabilityContractError(
                "LOCATE_NAMED_FILES requires one or more exact names"
            )
        params: dict[str, Any] = {
            "exact_names": [item.strip() for item in names],
            "locations": [cls._scope(entities)],
        }
        if "recursive" in entities:
            if not isinstance(entities["recursive"], bool):
                raise CapabilityContractError("recursive must be boolean")
            params["recursive"] = entities["recursive"]
        if "reveal_containing_folders" in entities:
            if not isinstance(entities["reveal_containing_folders"], bool):
                raise CapabilityContractError(
                    "reveal_containing_folders must be boolean"
                )
            params["reveal_containing_folders"] = entities[
                "reveal_containing_folders"
            ]
        return "fs.search_exact", params

    @classmethod
    def _reveal_directory(
        cls, entities: Mapping[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        params: dict[str, Any] = {"location": cls._scope(entities)}
        relative_path = entities.get("relative_path")
        if relative_path is not None:
            if not isinstance(relative_path, str) or not relative_path.strip():
                raise CapabilityContractError(
                    "relative_path must be a non-empty string"
                )
            params["relative_path"] = relative_path.strip()
        return "fs.reveal", params

    @classmethod
    def _list_local_items(
        cls, entities: Mapping[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        params: dict[str, Any] = {"locations": [cls._scope(entities)]}
        for key in ("item_kind", "sort", "recursive"):
            if key in entities:
                params[key] = entities[key]
        return "fs.list", params

    @staticmethod
    def _publish_exact_artifact(
        entities: Mapping[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        path = entities.get("path")
        content = entities.get("content")
        if not isinstance(path, str) or not path.strip():
            raise CapabilityContractError(
                "PUBLISH_EXACT_ARTIFACT requires path"
            )
        if not isinstance(content, str):
            raise CapabilityContractError(
                "PUBLISH_EXACT_ARTIFACT requires exact text content"
            )
        return "project.publish_exact_artifact", {
            "artifact_path": path.strip(),
            "artifact_content": content,
        }
