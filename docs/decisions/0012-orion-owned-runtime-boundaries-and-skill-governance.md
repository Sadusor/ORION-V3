# Decision 0012 — ORION-Owned Runtime Boundaries and Skill Governance

Date: 2026-10-04  
Status: OWNER-APPROVED DIRECTION  
Execution authorization: NONE IMPLIED

## Decision

ORION owns the safety and authority boundary around every active execution mode:

- sandboxed coding;
- Personal/Desktop Assistant actions;
- Project/Coding Assistant actions;
- future learned skills;
- future agent substrates such as DeepSeek Harness.

Models and skills may propose or perform work only through ORION-governed capabilities.

## Coding mode

Coding should default to a disposable sandbox/worktree controlled by ORION.

Inside the sandbox, ordinary development work may proceed with minimal interruption:

- inspect repository files;
- edit/create/delete files inside the workspace;
- run tests/build/lint;
- retry after failures;
- use already-qualified tools and skills.

ORION retains control of:

- sandbox creation/destruction;
- real-path scope enforcement;
- network/download policy;
- protected paths;
- resource/time/turn budgets;
- STOP;
- evidence;
- promotion of exact reviewed changes into the real project.

The coding model or Harness never promotes its own work into protected state.

## Assistant mode

The Personal Assistant remains more conservative because it acts on the owner's real machine and personal data.

ORION classifies requested actions into deterministic risk classes.

- GREEN: low-risk read/open/search/navigation actions may run directly when bounded to the owner's request.
- YELLOW: material writes, downloads, installs, external side effects, sensitive data access, or unusual scope require a warning and/or one compact confirmation.
- RED: destructive/system/security/credential/authority-changing actions are denied unless a separately defined high-risk owner-authorized procedure exists.

The assistant model may identify possible risk, but ORION makes the actual policy decision.

Warnings are a UX aid, not the security boundary. Prohibited actions must be technically blocked even if a model fails to warn.

## Skills

Future learned skills are treated as untrusted capability proposals until qualified by ORION.

A skill must not gain authority merely because:

- a model generated it;
- it succeeded once;
- it was learned from prior behavior;
- it appears in memory;
- it is installed by an agent framework.

ORION owns a Skill Registry containing, at minimum:

- stable skill id/version;
- source/provenance;
- code/content hash;
- allowed operations;
- allowed paths/scopes;
- network policy;
- required confirmation class;
- sandbox requirement;
- resource/time limits;
- evidence requirements;
- qualification status;
- revocation/disable state.

A learned skill may become reusable only after qualification against deterministic tests.

Skill learning therefore follows:

```text
observed successful workflow
        ↓
candidate skill
        ↓
ORION qualification
        ↓
approved bounded capability
        ↓
versioned registry entry
```

A skill update is a new version and does not inherit trust automatically.

## Risk notification

ORION should warn the owner before a YELLOW/high-risk boundary crossing, with a compact explanation of:

- what is about to happen;
- target/path/account;
- why it is needed;
- whether network/download/external side effect is involved;
- whether rollback is available.

For RED actions, the default behavior is deny, not merely warn.

## Consequence

The long-term architecture becomes:

```text
Owner
  ↓
Phone / STRATA UI
  ↓
Local model / cloud reasoning
  ↓
ORION AUTHORITY
  ├─ Personal Assistant policy
  ├─ Project/Sandbox policy
  ├─ Skill Registry
  ├─ Memory scope/provenance
  ├─ STOP
  └─ Evidence
       ↓
  deterministic Hands / qualified skills / agent substrate
```

This lets coding be highly autonomous inside a disposable boundary while keeping real-machine assistant actions and learned capabilities tightly governed.

## Non-decision

This does not declare the current sandbox, skill system, or agent framework production-safe.

Each must pass physical adversarial tests before unattended use.
