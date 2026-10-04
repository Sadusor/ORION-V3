# Decision 0003 — Donor contract patterns before E2E continuation

Date: 2026-10-04  
Status: PROBE PASS — CONTRACT PATTERNS ACCEPTED FOR E2E USE

## Context

Before continuing the current cloud -> ORION -> Hands end-to-end proof, the owner requested a fresh review of the newest forks and a physical test of the strongest donor ideas.

Reviewed newest forks:

- `Sadusor/CLI-Anything` (parent: `HKUDS/CLI-Anything`, Apache-2.0)
- `Sadusor/Octop` (parent: `TencentCloud/Octop`, MIT)
- `Sadusor/openmuse` (parent: `CopilotKit/openmuse`, MIT)
- `Sadusor/GhostTrack` (parent: `HunxByts/GhostTrack`, no license reported by GitHub)

Presence in this decision is not adoption.

## Findings

### CLI-Anything — HIGH priority Hands donor

Useful patterns:

- stateful, machine-readable CLI surfaces for software that was originally GUI-first;
- inspect-before-mutate commands;
- one logical operation per command;
- JSON output for agent/host consumption;
- real backend invocation instead of toy reimplementation;
- explicit return codes and output verification;
- session state, undo/redo, file locking;
- E2E tests that verify the real final artifact, not just process exit;
- preview bundle protocol with immutable artifacts, `manifest.json`, compact `summary.json`, and append-only `trajectory.json`.

ORION disposition:

- borrow Hand adapter shape and evidence/preview contracts;
- keep ORION as authority above the Hand;
- do not let a CLI harness self-authorize;
- retain stricter ORION path/scope/approval rules.

### OpenMuse — HIGH priority approval/task/evidence donor

Useful patterns:

- exact proposal hash is bound to human review;
- changed/stale proposal cannot reuse an old approval;
- owner/connection/version are part of the reviewed state;
- approval claim executes once under concurrency;
- uncertain external writes are recorded as uncertain and are not blindly retried;
- operation IDs/idempotency keys;
- persisted command receipts;
- bounded command time/output;
- isolated computer contract and explicit no-credential/no-host-mount rules.

ORION disposition:

- adapt the frozen-plan-hash approval pattern;
- adapt one-shot/idempotent execution receipts;
- adapt explicit uncertain-outcome semantics;
- do not adopt the CopilotKit/OpenMuse application stack as ORION authority.

### Octop — MEDIUM/HIGH priority security/plugin/remote donor

Useful patterns:

- configurable tool deny/allow controls;
- human-in-the-loop tool policy;
- filesystem/security policy;
- command guard catalog;
- plugin/skill architecture;
- browser/terminal/remote-desktop surfaces;
- ACP adapters to external coding agents;
- optional agent-team tools kept separate from default tool surfaces.

ORION disposition:

- study/adapt security policy, tool guard, plugin registry and remote patterns;
- do not adopt agent-team autonomy or in-memory agent inbox as ORION authority/state;
- ORION remains the durable authority and provenance plane.

### GhostTrack — NO ORION ADOPTION

Observed code is a small OSINT utility for IP, phone-number and username lookups. It does not provide a useful authority, execution, evidence or memory architecture for ORION. GitHub reports no license for the fork.

Disposition: ignore for ORION runtime.

## Combined architecture pattern to test

The next bounded proof intentionally combines the strongest donor lessons without importing the donor frameworks:

1. DeepSeek hostile-scope requirement: a model proposal that widens scope must be rejected.
2. OpenMuse-style frozen proposal hash: approval is bound to the exact immutable contract.
3. ORION authority gate: only ORION validates policy/scope and decides executability.
4. CLI-Anything-style Hand contract: deterministic operation with machine-readable receipt.
5. ORION evidence: verify exact artifact bytes/path/hash and prove the denied side effect never happened.
6. OpenMuse-style replay protection: the same approved operation does not execute twice.
7. Mutation after approval must fail hash binding.

## Probe rule

This is a contract probe, not a donor installation test.

No donor becomes runtime authority. No new framework is installed. No network call is required. No legacy Remote UI code is changed.

The probe must use a disposable ORION-owned test directory only.

## Required PASS gates

- HOSTILE_SCOPE_REJECTION
- FROZEN_PLAN_HASH
- APPROVAL_HASH_BINDING
- POST_APPROVAL_MUTATION_DENIED
- DETERMINISTIC_HAND_EXECUTION
- IDEMPOTENT_REPLAY
- EXACT_PATH_BYTES_HASH
- OUTSIDE_SCOPE_UNTOUCHED
- MACHINE_READABLE_RECEIPT
- NO_NETWORK_MODEL_DEPENDENCY

Any failed gate means the donor contract pattern is not accepted yet.

## Sequence decision

Run this donor contract probe before resuming the current Cloud E2E Brainstorm / full owner -> cloud -> ORION -> Hands proof.

After this probe passes:

1. resume cloud E2E brainstorming;
2. synthesize cloud + DeepSeek recommendations;
3. perform the human-approved hostile-scope physical E2E proof;
4. repeat with Qwen 9B;
5. benchmark OpenHands/OpenJarvis-style substrate vs Qwen 9B + deterministic Hands using the same frozen contract.


## Probe result

Physical run PASS:

- source SHA: `8971d855e0867f980afeebad7db7636d569f274f`
- session: `92c002cdf162`
- all required gates PASS
- Evidence Pack ready
- no network/model dependency during execution

Evidence record: `docs/evidence/2026-10-04-donor-contract-probe-pass.md`

This accepts the contract patterns for ORION's next E2E proof. It does not adopt donor runtimes as authority.
