from __future__ import annotations

import pytest

from orion_v3.capabilities import CapabilityContractError, inherited_registry_v0
from orion_v3.routing import (
    IntentCanonicalizer,
    IntentContractError,
    IntentResolver,
    ResolutionStatus,
    SemanticIntent,
    parse_intent_proposal,
)


def canonicalize(payload):
    proposal = parse_intent_proposal(payload)
    return IntentCanonicalizer().canonicalize(proposal)


def resolve(payload):
    canonical = canonicalize(payload)
    return IntentResolver(inherited_registry_v0()).resolve(canonical)


def test_model_intent_contract_rejects_authority_and_capability_fields():
    for forbidden in (
        "capability",
        "capability_id",
        "implementation",
        "approval_class",
        "effect_class",
        "trusted_root",
        "allow_network",
        "skip_verification",
        "confidence",
    ):
        with pytest.raises(IntentContractError):
            parse_intent_proposal(
                {
                    "intent": "OPEN_WEB_URL",
                    "entities": {"url": "https://example.com"},
                    "ambiguities": [],
                    "composition": False,
                    forbidden: "model-controlled",
                }
            )


def test_locate_named_files_maps_deterministically_to_exact_search():
    result = resolve(
        {
            "intent": "LOCATE_NAMED_FILES",
            "entities": {
                "names": ["README.md", "pyproject.toml"],
                "scope": "active_project",
            },
            "ambiguities": [],
            "composition": False,
        }
    )
    assert result.status == ResolutionStatus.RESOLVED
    assert result.capability_id == "fs.search_exact"
    assert result.params == {
        "exact_names": ["README.md", "pyproject.toml"],
        "locations": ["active_project"],
        "recursive": True,
        "max_depth": 4,
        "max_results": 50,
        "reveal_containing_folders": False,
    }


def test_nonrecursive_and_reveal_modifiers_are_resolved_by_rules():
    result = resolve(
        {
            "intent": "LOCATE_NAMED_FILES",
            "entities": {
                "names": ["todo.txt"],
                "scope": "desktop",
                "recursive": False,
                "reveal_containing_folders": True,
            },
            "ambiguities": [],
            "composition": False,
        }
    )
    assert result.capability_id == "fs.search_exact"
    assert result.params["recursive"] is False
    assert result.params["reveal_containing_folders"] is True


def test_list_intent_can_never_select_exact_search():
    result = resolve(
        {
            "intent": "LIST_LOCAL_ITEMS",
            "entities": {
                "scope": "downloads",
                "item_kind": "files",
                "sort": "newest_modified",
            },
            "ambiguities": [],
            "composition": False,
        }
    )
    assert result.status == ResolutionStatus.RESOLVED
    assert result.capability_id == "fs.list"


def test_recognized_but_unimplemented_intent_returns_no_capability():
    result = resolve(
        {
            "intent": "CLOSE_APP",
            "entities": {"app": "chrome"},
            "ambiguities": [],
            "composition": False,
        }
    )
    assert result.status == ResolutionStatus.NO_CAPABILITY
    assert result.capability_id is None
    assert result.params == {}


def test_destructive_semantic_intent_is_understood_but_not_dispatched():
    result = resolve(
        {
            "intent": "DELETE_LOCAL_ITEMS",
            "entities": {"scope": "downloads", "selector": "all"},
            "ambiguities": [],
            "composition": False,
        }
    )
    assert result.status == ResolutionStatus.NO_CAPABILITY
    assert result.capability_id is None


def test_ambiguity_and_composition_never_dispatch():
    ambiguous = resolve(
        {
            "intent": None,
            "entities": {},
            "ambiguities": ["Missing referent for 'it'."],
            "composition": False,
        }
    )
    assert ambiguous.status == ResolutionStatus.AMBIGUOUS

    composition = resolve(
        {
            "intent": None,
            "entities": {},
            "ambiguities": [],
            "composition": True,
        }
    )
    assert composition.status == ResolutionStatus.AMBIGUOUS


def test_untrusted_scope_cannot_be_promoted_to_trusted_location():
    with pytest.raises(CapabilityContractError):
        resolve(
            {
                "intent": "LOCATE_NAMED_FILES",
                "entities": {"names": ["README.md"], "scope": "C:/"},
                "ambiguities": [],
                "composition": False,
            }
        )


def test_publish_exact_content_preserves_whitespace_through_resolver():
    payload = "  first line\nsecond line\n"
    result = resolve(
        {
            "intent": "PUBLISH_EXACT_ARTIFACT",
            "entities": {"path": "docs/example.txt", "content": payload},
            "ambiguities": [],
            "composition": False,
        }
    )
    assert result.capability_id == "project.publish_exact_artifact"
    assert result.params["artifact_content"] == payload


def test_canonicalizer_drops_optional_null_and_normalizes_aliases():
    canonical = canonicalize(
        {
            "intent": "RESTART_ORION",
            "entities": {"component": None},
            "ambiguities": [],
            "composition": False,
        }
    )
    assert canonical.entities == {}

    canonical = canonicalize(
        {
            "intent": "DELETE_LOCAL_ITEMS",
            "entities": {"scope": "My Downloads", "selector": "every"},
            "ambiguities": [],
            "composition": False,
        }
    )
    assert canonical.entities == {"scope": "downloads", "selector": "all"}


def test_canonicalizer_separates_policy_intrusions_from_semantic_ambiguity():
    canonical = canonicalize(
        {
            "intent": "DELETE_LOCAL_ITEMS",
            "entities": {"scope": "downloads", "selector": "every"},
            "ambiguities": [
                "Does every file include hidden files?",
                "Are you sure you want to delete them?",
                "Shell commands are not permitted.",
            ],
            "composition": False,
        }
    )
    assert canonical.ambiguities == ("Does every file include hidden files?",)
    assert canonical.policy_intrusions == (
        "Are you sure you want to delete them?",
        "Shell commands are not permitted.",
    )


def test_canonicalizer_preserves_exact_artifact_content():
    payload = "  exact body\n"
    canonical = canonicalize(
        {
            "intent": "PUBLISH_EXACT_ARTIFACT",
            "entities": {"path": "docs/x.txt", "content": payload},
            "ambiguities": [],
            "composition": False,
        }
    )
    assert canonical.entities["content"] == payload


def test_resolver_can_understand_destructive_intent_without_dispatch():
    result = resolve(
        {
            "intent": "DELETE_LOCAL_ITEMS",
            "entities": {"scope": "downloads", "selector": "every"},
            "ambiguities": [],
            "composition": False,
        }
    )
    assert result.status == ResolutionStatus.NO_CAPABILITY
    assert result.capability_id is None
