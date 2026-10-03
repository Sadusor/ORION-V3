# V3-RUN-010 — Semantic Capability Contract Physical PASS

Date: 2026-10-03

Status: **PHYSICAL PASS**

## Identity

ORION-V3 exact tested SHA:

`c6f5ab1b90af685f38288ce0211571d5d7098d0b`

Legacy ORION Remote transport task SHA:

`17fb13093b15c5f7e6c1957d958a5f745ad08400`

Legacy Remote transport attempt:

`410`

The Remote attempt number is transport evidence only. It is not the V3 run number.

## Physical result

Remote runner result:

`PASS`

Runner exit code:

`0`

V3 regression:

`42 passed in 0.60s`

## Contract falsifiers

Observed:

- `LEGACY_PROVEN_CAPABILITIES_IMPORTED> PASS`
- `EXPERIMENTAL_STATUS_NOT_OVERCLAIMED> PASS`
- `MODEL_POLICY_FIELD_INJECTION> DENIED`
- `UNKNOWN_CAPABILITY> DENIED`
- `RAW_SHELL_PARAMETER> DENIED`
- `TYPED_DEFAULTS_AND_BOUNDS> PASS`
- `TRUSTED_LOCATION_SCOPE> PASS`
- `AMBIGUITY_FAIL_CLOSED> PASS`
- `SEMANTIC_CAPABILITY_CONTRACT> PASS`

Imported capability status:

- `browser.open_url` — PROVEN_ACTIVE / REVERSIBLE_ROUTINE / approval 1
- `fs.search_exact` — PROVEN_ACTIVE / READ_ONLY / approval 0
- `fs.reveal` — PROVEN_ACTIVE / REVERSIBLE_ROUTINE / approval 1
- `project.publish_exact_artifact` — PROVEN_ACTIVE / BOUNDED_MODIFICATION / approval 2
- `fs.list` — EXPERIMENTAL / READ_ONLY / approval 0

## Architectural significance

This physically proves the first V3 semantic-policy layer without creating a
second low-level Hand framework.

The model-facing request boundary accepts semantic intent/params/ambiguity only.
It does not accept authority, policy, trusted host roots, implementation choice
or arbitrary shell parameters.

The physically proven legacy capabilities are carried forward as semantic
records while their concrete implementations remain donor/legacy-owned.

This is the intended separation:

```text
Qwen semantic intent
-> ORION deterministic capability policy
-> vetted implementation
-> evidence
-> verifier
```

## V3-RUN-009

The staged primitive OpenHands adapter was **not executed**.

Observed physical marker:

`V3_RUN_009> INTENTIONALLY_NOT_EXECUTED`

This preserves the architecture correction: do not resume primitive coding-Hand
wrapping as the default direction.

## Next experiment

V3-RUN-011 should benchmark Qwen3.5-9B on natural-language requests mapping to:

- semantic intent;
- typed parameters;
- ambiguity when necessary;

with these constraints:

- no PowerShell;
- no implementation selection;
- no approval/effect-class generation;
- no authority fields;
- deterministic scoring against a fixed labeled corpus;
- token/latency capture;
- out-of-registry requests must escalate/mark unknown rather than hallucinate a
  capability.

The purpose is to test Qwen as the lightweight everyday semantic governor.
