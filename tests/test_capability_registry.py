from __future__ import annotations

import pytest

from orion_v3.capabilities import (
    ApprovalClass,
    CapabilityContractError,
    CapabilityStatus,
    EffectClass,
    inherited_registry_v0,
    parse_model_proposal,
)


def resolve(payload):
    registry = inherited_registry_v0()
    proposal = parse_model_proposal(payload)
    return registry.resolve(proposal)


def test_inherited_registry_preserves_physically_proven_legacy_capabilities():
    registry = inherited_registry_v0()
    snapshot = registry.snapshot()

    expected = {
        "project.publish_exact_artifact",
        "browser.open_url",
        "fs.search_exact",
        "fs.reveal",
        "fs.list",
    }
    assert set(snapshot) == expected

    assert snapshot["project.publish_exact_artifact"].status == CapabilityStatus.PROVEN_ACTIVE
    assert snapshot["browser.open_url"].status == CapabilityStatus.PROVEN_ACTIVE
    assert snapshot["fs.search_exact"].status == CapabilityStatus.PROVEN_ACTIVE
    assert snapshot["fs.reveal"].status == CapabilityStatus.PROVEN_ACTIVE
    assert snapshot["fs.list"].status == CapabilityStatus.EXPERIMENTAL


def test_qwen_proposal_can_only_supply_intent_params_or_ambiguity():
    for forbidden in (
        "approval_class",
        "effect_class",
        "trusted_root",
        "repo_root",
        "allow_network",
        "credentials",
        "implementation",
        "skip_verification",
    ):
        with pytest.raises(CapabilityContractError):
            parse_model_proposal(
                {
                    "intent": "browser.open_url",
                    "params": {"url": "https://example.com"},
                    forbidden: "attacker-controlled",
                }
            )


def test_unknown_capability_fails_closed():
    with pytest.raises(CapabilityContractError, match="Unknown ORION capability"):
        resolve({"intent": "shell.run_anything", "params": {}})


def test_unknown_parameter_fails_closed():
    with pytest.raises(CapabilityContractError, match="Unknown parameter"):
        resolve(
            {
                "intent": "browser.open_url",
                "params": {
                    "url": "https://example.com",
                    "powershell": "Remove-Item C:/ -Recurse",
                },
            }
        )


def test_browser_open_url_defaults_to_default_browser():
    resolved = resolve(
        {
            "intent": "browser.open_url",
            "params": {"url": "https://example.com"},
        }
    )
    assert resolved.params == {
        "url": "https://example.com",
        "browser": "default",
    }
    assert resolved.definition.effect_class == EffectClass.REVERSIBLE_ROUTINE
    assert resolved.definition.approval_class == ApprovalClass.REVERSIBLE_ROUTINE


def test_file_search_defaults_and_bounds():
    resolved = resolve(
        {
            "intent": "fs.search_exact",
            "params": {
                "exact_names": ["README.md"],
                "locations": ["active_project"],
            },
        }
    )
    assert resolved.params["recursive"] is True
    assert resolved.params["max_depth"] == 4
    assert resolved.params["max_results"] == 50
    assert resolved.params["reveal_containing_folders"] is False

    with pytest.raises(CapabilityContractError):
        resolve(
            {
                "intent": "fs.search_exact",
                "params": {
                    "exact_names": ["README.md"],
                    "locations": ["C:/"],
                },
            }
        )


def test_ambiguity_does_not_resolve_to_execution():
    proposal = parse_model_proposal(
        {
            "intent": None,
            "params": {},
            "ambiguity": "Two projects were named.",
        }
    )
    with pytest.raises(CapabilityContractError, match="Ambiguous proposal"):
        inherited_registry_v0().resolve(proposal)


def test_model_cannot_mix_intent_and_ambiguity():
    with pytest.raises(CapabilityContractError):
        parse_model_proposal(
            {
                "intent": "fs.search_exact",
                "params": {},
                "ambiguity": "Maybe another task.",
            }
        )


def test_experimental_capability_is_visible_but_not_claimed_proven():
    definition = inherited_registry_v0().get("fs.list")
    assert definition.status == CapabilityStatus.EXPERIMENTAL
    assert definition.validated_sha is None
    assert definition.physical_evidence_refs == ()


def test_exact_artifact_content_preserves_leading_and_trailing_whitespace():
    payload = "  first line\nsecond line\n"
    resolved = resolve(
        {
            "intent": "project.publish_exact_artifact",
            "params": {
                "artifact_path": "docs/example.txt",
                "artifact_content": payload,
            },
        }
    )
    assert resolved.params["artifact_content"] == payload
