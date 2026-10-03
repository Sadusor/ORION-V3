from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .intent import IntentProposal, SemanticIntent


@dataclass(frozen=True)
class CanonicalIntent:
    intent: SemanticIntent | None
    entities: Mapping[str, Any]
    ambiguities: tuple[str, ...]
    composition: bool
    policy_intrusions: tuple[str, ...] = ()
    contract_violations: tuple[str, ...] = ()


_ALLOWED_ENTITY_KEYS = {
    SemanticIntent.OPEN_WEB_URL: {"url", "browser"},
    SemanticIntent.LOCATE_NAMED_FILES: {
        "names", "scope", "recursive", "reveal_containing_folders"
    },
    SemanticIntent.REVEAL_DIRECTORY: {"scope", "relative_path"},
    SemanticIntent.LIST_LOCAL_ITEMS: {
        "scope", "item_kind", "sort", "recursive"
    },
    SemanticIntent.PUBLISH_EXACT_ARTIFACT: {"path", "content"},
    SemanticIntent.OPEN_APP: {"app"},
    SemanticIntent.CLOSE_APP: {"app"},
    SemanticIntent.RESTART_ORION: {"component"},
    SemanticIntent.RUN_PROJECT_TESTS: {"project"},
    SemanticIntent.DELETE_LOCAL_ITEMS: {"scope", "target", "selector"},
    SemanticIntent.GET_WEATHER: {"location"},
    SemanticIntent.SYSTEM_STATUS: {"subject"},
}

_SCOPE_ALIASES = {
    "desktop": "desktop",
    "my desktop": "desktop",
    "downloads": "downloads",
    "my downloads": "downloads",
    "documents": "documents",
    "my documents": "documents",
    "active project": "active_project",
    "active_project": "active_project",
    "current project": "active_project",
    "orion artifacts": "orion_artifacts",
    "orion_artifacts": "orion_artifacts",
}

_APP_ALIASES = {
    "google chrome": "chrome",
    "chrome": "chrome",
    "microsoft edge": "edge",
    "edge": "edge",
    "ollama": "ollama",
    "orion": "orion",
}

_SELECTOR_ALIASES = {
    "all": "all",
    "every": "all",
    "everything": "all",
    "all files": "all",
    "every file": "all",
}

_ITEM_KIND_ALIASES = {
    "file": "files",
    "files": "files",
    "folder": "folders",
    "folders": "folders",
    "directory": "folders",
    "directories": "folders",
    "both": "both",
    "files and folders": "both",
}

_SORT_ALIASES = {
    "newest": "newest_modified",
    "latest": "newest_modified",
    "newest_modified": "newest_modified",
    "oldest": "oldest_modified",
    "oldest_modified": "oldest_modified",
}

_POLICY_AMBIGUITY_MARKERS = (
    "are you sure",
    "are you certain",
    "certainty",
    "confirmation",
    "confirm",
    "permission",
    "permitted",
    "not permitted",
    "authorization",
    "authoriz",
    "policy",
    "safety",
    "safe to",
    "allowed to",
    "capability",
    "shell commands",
    "powershell is not",
)


def _clean_string(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    return value.strip()


def _alias(value: Any, aliases: Mapping[str, str]) -> Any:
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    return aliases.get(stripped.casefold(), stripped)


def _is_policy_intrusion(text: str) -> bool:
    lowered = text.casefold()
    return any(marker in lowered for marker in _POLICY_AMBIGUITY_MARKERS)


class IntentCanonicalizer:
    """Deterministically regularize literal model semantics before resolution."""

    def canonicalize(self, proposal: IntentProposal) -> CanonicalIntent:
        entities = {
            key: value
            for key, value in proposal.entities.items()
            if value is not None
        }

        violations: list[str] = []
        if proposal.intent is not None:
            allowed = _ALLOWED_ENTITY_KEYS.get(proposal.intent, set())
            unknown = sorted(set(entities) - allowed)
            if unknown:
                violations.append(
                    "unknown entity field(s): " + ", ".join(unknown)
                )
                for key in unknown:
                    entities.pop(key, None)

        entities = self._canonical_entities(proposal.intent, entities)

        semantic_ambiguities: list[str] = []
        policy_intrusions: list[str] = []
        for ambiguity in proposal.ambiguities:
            if _is_policy_intrusion(ambiguity):
                policy_intrusions.append(ambiguity)
            else:
                semantic_ambiguities.append(ambiguity)

        return CanonicalIntent(
            intent=proposal.intent,
            entities=entities,
            ambiguities=tuple(semantic_ambiguities),
            composition=proposal.composition,
            policy_intrusions=tuple(policy_intrusions),
            contract_violations=tuple(violations),
        )

    def _canonical_entities(
        self,
        intent: SemanticIntent | None,
        entities: Mapping[str, Any],
    ) -> dict[str, Any]:
        out = dict(entities)

        if "scope" in out:
            out["scope"] = _alias(out["scope"], _SCOPE_ALIASES)

        if "app" in out:
            out["app"] = _alias(out["app"], _APP_ALIASES)

        if "browser" in out:
            out["browser"] = _alias(
                out["browser"],
                {"google chrome": "chrome", "chrome": "chrome", "default": "default"},
            )

        if "selector" in out:
            out["selector"] = _alias(out["selector"], _SELECTOR_ALIASES)

        if "item_kind" in out:
            out["item_kind"] = _alias(out["item_kind"], _ITEM_KIND_ALIASES)

        if "sort" in out:
            out["sort"] = _alias(out["sort"], _SORT_ALIASES)

        if "names" in out and isinstance(out["names"], list):
            out["names"] = [
                item.strip() if isinstance(item, str) else item
                for item in out["names"]
            ]

        for key in ("url", "relative_path", "path", "project", "location", "target", "component", "subject"):
            if key in out:
                out[key] = _clean_string(out[key])

        # Exact artifact content must never be stripped or rewritten.
        if intent == SemanticIntent.PUBLISH_EXACT_ARTIFACT and "content" in entities:
            out["content"] = entities["content"]

        return out
