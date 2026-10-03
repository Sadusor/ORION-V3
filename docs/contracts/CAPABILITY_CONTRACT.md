# ORION Semantic Capability Contract v0

Status: **DESIGN CONTRACT / NOT YET PHYSICALLY QUALIFIED**

Date: 2026-10-03

This contract defines the ORION-level semantic capability abstraction.

It is intentionally different from a donor ToolRegistry.

- Donor ToolRegistry: concrete callable tools/implementations.
- ORION Capability Registry: stable intent + typed inputs + policy + evidence
  contract + implementation binding.

## Purpose

A model should normally emit:

```json
{
  "intent": "app.open",
  "params": {
    "app": "chrome"
  }
}
```

It should not normally emit:

```text
Start-Process chrome.exe
```

ORION resolves the semantic intent to one vetted implementation according to
deterministic policy.

## Capability record

Each promoted capability must define:

```text
capability_id
version
purpose
status
parameter_schema
effect_class
approval_class
allowed_scopes
binding_requirements
implementation_candidates
active_implementation
availability_probe
preconditions
stop_contract
evidence_contract
postconditions
resource_profile
provenance
validated_sha
physical_evidence_refs
replaces
fallback
```

## Required fields

### capability_id

Stable semantic identifier.

Examples:
- `browser.open_url`
- `fs.search_exact`
- `project.run_tests`
- `orion.remote.restart`

The ID describes intent, not implementation technology.

Bad:
`powershell.start_process`

Good:
`app.open`

### version

Contract version for this semantic capability.

Changing implementation alone does not require changing the semantic ID if the
same contract still holds.

### purpose

Human-readable concise capability goal.

### status

One of:

- `EXPERIMENTAL`
- `PROVEN_ACTIVE`
- `FROZEN_FALLBACK`
- `RETIRED`
- `BLOCKED`

A capability is not `PROVEN_ACTIVE` merely because its donor exists.

### parameter_schema

Typed and bounded request parameters.

Rules:
- no arbitrary raw shell field for normal semantic capabilities;
- no host absolute paths when a logical project/location binding can be used;
- enumerate finite choices where practical;
- bound strings, arrays, recursion depth, counts and output sizes;
- reject unknown parameters by default.

### effect_class

Small deterministic classification of side effects.

Initial classes:

- `READ_ONLY`
- `REVERSIBLE_ROUTINE`
- `BOUNDED_MODIFICATION`
- `CONSEQUENTIAL`

Effect class is policy metadata, not a model judgment.

### approval_class

Initial mapping:

- Class 0 — read-only: direct user request is sufficient.
- Class 1 — reversible routine: direct unambiguous user request normally
  sufficient.
- Class 2 — bounded modification: parent Task/Action Lease may authorize the
  whole bounded operation/workflow.
- Class 3 — consequential: stronger explicit scope/confirmation unless the
  direct user instruction is itself the exact unambiguous requested effect.

Approval is determined by ORION policy.

### allowed_scopes

What the capability may affect.

Examples:
- named project binding;
- named filesystem location;
- exact process/app registry entry;
- exact network destination category;
- exact device;
- exact repository/branch.

Scope must be representable without trusting model-generated host paths.

### binding_requirements

Required trusted ORION-side bindings before dispatch.

Examples:
- project link ready;
- application registry entry exists;
- device ID already paired;
- repository identity/branch known;
- URL protocol allowed.

Models cannot supply/override trusted bindings.

### implementation_candidates

Replaceable concrete implementations.

Example:

```text
browser.open_url
  -> legacy_orion.open_web_url
  -> openjarvis.browser_open
  -> future native Windows browser adapter
```

### active_implementation

Current policy-selected implementation.

Qwen does not choose this field.

### availability_probe

Cheap deterministic check that the implementation can currently run.

Examples:
- executable exists;
- service is reachable;
- project link is READY;
- donor worker installed;
- required local endpoint responds.

### preconditions

Conditions that must be verified **before** any effect.

Examples:
- typed params validate;
- target maps to trusted binding;
- repo branch and SHA match;
- target process/app identity is exact;
- no unrelated staged changes;
- URL scheme is HTTP/HTTPS;
- direct request/Task lease satisfies approval class.

A post-execution verifier is not a substitute for pre-effect validation.

### stop_contract

How the operation can be stopped and what STOPPED means.

Must state:
- owned process/session identity;
- how cancellation is delivered;
- child-process semantics;
- timeout relationship;
- how termination is verified;
- whether rollback is possible/required.

Timeout != Stop.

### evidence_contract

Exact evidence required from the implementation.

Examples:
- PID/process existence;
- final URL/host;
- local/remote Git SHA;
- changed file hash;
- test command + exit code;
- file search scope/results;
- process absence after Stop.

Implementation prose is not enough.

### postconditions

Independent checks ORION performs after implementation returns.

Examples:
- remote SHA == local HEAD;
- target process exists;
- target process is gone;
- file bytes/hash equal authorized content;
- test suite exit code == 0;
- no changed paths outside allowed scope.

### resource_profile

Optional expected:
- wall-time class;
- CPU/RAM/GPU;
- network;
- model/API use;
- paid/free status.

This supports cheapest-sufficient implementation selection.

### provenance

Where the implementation came from.

Examples:
- legacy ORION Remote;
- OpenJarvis;
- OpenMuse;
- OpenHands;
- native Windows;
- ORION custom gap.

### validated_sha

Exact implementation revision last physically qualified.

### physical_evidence_refs

Pointers to immutable/frozen evidence.

A capability without physical evidence may still exist as `EXPERIMENTAL`, but
must not silently become `PROVEN_ACTIVE`.

### replaces / fallback

Record migration history so V3 can switch implementations without losing the
known-good fallback.

## Request envelope

Qwen-facing normal request:

```json
{
  "intent": "fs.search_exact",
  "params": {
    "names": ["example.md"],
    "locations": ["active_project"]
  },
  "ambiguity": null
}
```

Qwen may also report:

```json
{
  "intent": null,
  "params": {},
  "ambiguity": "The user named two projects and did not say which one."
}
```

No authority fields are accepted from the model.

Forbidden model-supplied examples:
- `approval_class`
- `effect_class`
- `trusted_root`
- `repo_root`
- `allow_network`
- `credentials`
- `implementation`
- `skip_verification`

## Resolution pipeline

```text
1. user request
2. Qwen -> typed intent/entities/ambiguity
3. ORION registry lookup
4. deterministic capability match
5. parameter schema validation
6. trusted binding resolution
7. effect + approval policy
8. availability/health
9. precondition checks
10. active implementation dispatch
11. evidence capture
12. postcondition verification
13. PASS/FAIL/STOPPED/BLOCKED
14. event log + Memory Gate
```

## Escalation

If no exact capability fits:

1. known workflow;
2. small validated composition;
3. bounded cloud reasoning for analysis;
4. Coding Factory for project-development work;
5. Whole-PC Computer Hand for novel GUI work.

Qwen does not jump directly to a high-cost rung simply because it is available.

## Composition contract

A small composition may contain only registered capabilities.

ORION validates:
- typed outputs/inputs between steps;
- no cycles;
- combined effect class;
- combined scope;
- budget;
- Stop behavior;
- approval sufficiency.

Do not allow Qwen to hide arbitrary shell inside a "workflow" step.

## Guard contract

Guard logic is split:

### Before effect
- semantic capability known;
- schema valid;
- scope valid;
- approval valid;
- implementation available;
- implementation preconditions valid.

### During effect
- containment / exact argv / trusted API where practical;
- no untrusted shell interpolation;
- owned processes/sessions tracked.

### After effect
- evidence schema valid;
- postconditions independently checked;
- result normalized.

The implementation is considered buggy if it escapes its declared contract,
even if the final user-visible outcome looks correct.

## Direct user request as approval

Avoid redundant confirmations.

Examples:

`"Open Chrome"`
-> `app.open(chrome)`
-> Class 1
-> direct request is approval.

`"Run PayDay tests"`
-> `project.run_tests(PayDay)`
-> Class 1/2 depending on test side effects
-> parent request/task may authorize execution.

`"Shut down the PC"`
-> `system.shutdown`
-> Class 3
-> the exact direct, unambiguous request can itself be the approval for that
exact effect if policy permits.

A vague statement such as `"I'm done for today"` does not authorize shutdown.

## Compatibility lane

Legacy raw PowerShell remains a compatibility/development path.

It is not a semantic capability for Qwen to use casually.

Use it when:
- capability is genuinely absent;
- one-off bounded experiment is explicitly approved;
- evidence/Stop contract is defined.

Repeated successful raw-shell tasks should be considered for deterministic
capability promotion.

## Promotion policy

A trace does not become trusted code automatically.

Candidate promotion requires:
- same task class succeeds repeatedly (initial policy target: >=3 independent
  successes);
- task/environment is sufficiently stable;
- deterministic typed extraction is possible;
- candidate implementation has explicit pre/evidence/post contracts;
- candidate passes the prior cases;
- scope/security review;
- human/policy promotion decision.

Do not promote workflows that still require visual/human/semantic judgment.

## Initial inherited capabilities

See `docs/CAPABILITY_INVENTORY.md`.

First V3 migration targets:
- `project.publish_exact_artifact`
- `browser.open_url`
- `fs.search_exact`
- `fs.reveal`
- `fs.list` (requires requalification)

Then harvest lifecycle/project/Ollama/dev operations behind the same contract.

## Acceptance criteria for Capability Contract v0 implementation

Before claiming the new registry physically proven:

1. unknown capability denied;
2. unknown params denied;
3. model cannot set policy/binding/implementation fields;
4. direct Class-0/Class-1 request avoids redundant approval;
5. scope mismatch blocked before implementation;
6. implementation cannot receive untrusted host path when logical binding exists;
7. exact implementation identity recorded;
8. evidence contract checked;
9. postcondition checked;
10. Stop semantics defined per side-effecting capability;
11. fallback/provenance preserved;
12. Qwen routing can choose the semantic intent without emitting shell.

No giant capability batch should be implemented until this core contract passes
on a small inherited set.
