from __future__ import annotations

from orion_v3.capabilities import (
    ApprovalClass,
    CapabilityContractError,
    CapabilityStatus,
    EffectClass,
    inherited_registry_v0,
    parse_model_proposal,
)


print("V3_RUN_ID> V3-RUN-010")
print("SEMANTIC_CAPABILITY_CONTRACT> START")

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

for capability_id in (
    "project.publish_exact_artifact",
    "browser.open_url",
    "fs.search_exact",
    "fs.reveal",
):
    assert snapshot[capability_id].status == CapabilityStatus.PROVEN_ACTIVE
assert snapshot["fs.list"].status == CapabilityStatus.EXPERIMENTAL

print("LEGACY_PROVEN_CAPABILITIES_IMPORTED> PASS")
print("EXPERIMENTAL_STATUS_NOT_OVERCLAIMED> PASS")

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
    try:
        parse_model_proposal(
            {
                "intent": "browser.open_url",
                "params": {"url": "https://example.com"},
                forbidden: "attacker-controlled",
            }
        )
    except CapabilityContractError:
        pass
    else:
        raise AssertionError(f"model injected forbidden policy field: {forbidden}")

print("MODEL_POLICY_FIELD_INJECTION> DENIED")

try:
    registry.resolve(
        parse_model_proposal(
            {"intent": "shell.run_anything", "params": {}}
        )
    )
except CapabilityContractError:
    pass
else:
    raise AssertionError("unknown capability unexpectedly resolved")

print("UNKNOWN_CAPABILITY> DENIED")

try:
    registry.resolve(
        parse_model_proposal(
            {
                "intent": "browser.open_url",
                "params": {
                    "url": "https://example.com",
                    "powershell": "Remove-Item C:/ -Recurse",
                },
            }
        )
    )
except CapabilityContractError:
    pass
else:
    raise AssertionError("unknown raw-shell parameter unexpectedly accepted")

print("RAW_SHELL_PARAMETER> DENIED")

browser = registry.resolve(
    parse_model_proposal(
        {
            "intent": "browser.open_url",
            "params": {"url": "https://example.com"},
        }
    )
)
assert browser.params["browser"] == "default"
assert browser.definition.effect_class == EffectClass.REVERSIBLE_ROUTINE
assert browser.definition.approval_class == ApprovalClass.REVERSIBLE_ROUTINE

search = registry.resolve(
    parse_model_proposal(
        {
            "intent": "fs.search_exact",
            "params": {
                "exact_names": ["README.md"],
                "locations": ["active_project"],
            },
        }
    )
)
assert search.params["recursive"] is True
assert search.params["max_depth"] == 4
assert search.params["max_results"] == 50
assert search.params["reveal_containing_folders"] is False

print("TYPED_DEFAULTS_AND_BOUNDS> PASS")

try:
    registry.resolve(
        parse_model_proposal(
            {
                "intent": "fs.search_exact",
                "params": {
                    "exact_names": ["README.md"],
                    "locations": ["C:/"],
                },
            }
        )
    )
except CapabilityContractError:
    pass
else:
    raise AssertionError("untrusted absolute root unexpectedly accepted")

print("TRUSTED_LOCATION_SCOPE> PASS")

ambiguous = parse_model_proposal(
    {
        "intent": None,
        "params": {},
        "ambiguity": "Two projects were named and no target was selected.",
    }
)
try:
    registry.resolve(ambiguous)
except CapabilityContractError:
    pass
else:
    raise AssertionError("ambiguous proposal unexpectedly dispatched")

print("AMBIGUITY_FAIL_CLOSED> PASS")

for capability_id, definition in sorted(snapshot.items()):
    print(
        "CAPABILITY> "
        + capability_id
        + " | "
        + definition.status.value
        + " | "
        + definition.effect_class.value
        + " | approval="
        + str(int(definition.approval_class))
        + " | impl="
        + str(definition.active_implementation)
    )

print("SEMANTIC_CAPABILITY_CONTRACT> PASS")
print("STATUS> PASS")
