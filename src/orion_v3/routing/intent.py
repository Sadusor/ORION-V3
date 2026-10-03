from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class IntentContractError(ValueError):
    """A model-produced semantic intent violated the ORION contract."""


class SemanticIntent(str, Enum):
    OPEN_WEB_URL = "OPEN_WEB_URL"
    LOCATE_NAMED_FILES = "LOCATE_NAMED_FILES"
    REVEAL_DIRECTORY = "REVEAL_DIRECTORY"
    LIST_LOCAL_ITEMS = "LIST_LOCAL_ITEMS"
    PUBLISH_EXACT_ARTIFACT = "PUBLISH_EXACT_ARTIFACT"
    OPEN_APP = "OPEN_APP"
    CLOSE_APP = "CLOSE_APP"
    RESTART_ORION = "RESTART_ORION"
    RUN_PROJECT_TESTS = "RUN_PROJECT_TESTS"
    DELETE_LOCAL_ITEMS = "DELETE_LOCAL_ITEMS"
    GET_WEATHER = "GET_WEATHER"
    SYSTEM_STATUS = "SYSTEM_STATUS"


@dataclass(frozen=True)
class IntentProposal:
    intent: SemanticIntent | None
    entities: Mapping[str, Any]
    ambiguities: tuple[str, ...]
    composition: bool


_ALLOWED_TOP_LEVEL = frozenset(
    {"intent", "entities", "ambiguities", "composition"}
)


def parse_intent_proposal(payload: Mapping[str, Any]) -> IntentProposal:
    if not isinstance(payload, Mapping):
        raise IntentContractError("Intent proposal must be an object")

    unknown = set(payload) - _ALLOWED_TOP_LEVEL
    if unknown:
        raise IntentContractError(
            "Intent proposal contains forbidden/unknown field(s): "
            + ", ".join(sorted(unknown))
        )

    raw_intent = payload.get("intent")
    if raw_intent is None:
        intent = None
    else:
        if not isinstance(raw_intent, str):
            raise IntentContractError("intent must be a string or null")
        try:
            intent = SemanticIntent(raw_intent.strip())
        except ValueError as exc:
            raise IntentContractError(
                f"Unknown semantic intent: {raw_intent!r}"
            ) from exc

    entities = payload.get("entities", {})
    if not isinstance(entities, Mapping):
        raise IntentContractError("entities must be an object")

    raw_ambiguities = payload.get("ambiguities", [])
    if not isinstance(raw_ambiguities, list):
        raise IntentContractError("ambiguities must be an array")
    ambiguities: list[str] = []
    for item in raw_ambiguities:
        if not isinstance(item, str) or not item.strip():
            raise IntentContractError(
                "ambiguities must contain non-empty strings"
            )
        ambiguities.append(item.strip())

    composition = payload.get("composition", False)
    if not isinstance(composition, bool):
        raise IntentContractError("composition must be boolean")

    if intent is None and not ambiguities and not composition:
        raise IntentContractError(
            "Proposal requires an intent, ambiguity, or composition marker"
        )

    return IntentProposal(
        intent=intent,
        entities=dict(entities),
        ambiguities=tuple(ambiguities),
        composition=composition,
    )
