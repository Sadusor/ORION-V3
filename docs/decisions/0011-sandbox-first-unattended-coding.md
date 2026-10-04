# Decision 0011 — Sandbox-First Unattended Coding

Date: 2026-10-04  
Status: OWNER-APPROVED DIRECTION  
Execution authorization: NONE IMPLIED

## Decision

Move most coding risk out of repeated per-action approvals and into a strong execution boundary.

Inside an approved disposable coding workspace, ORION may allow a coding model / agent substrate to work with much less owner interruption.

Crossing the workspace boundary remains an ORION authority decision.

The target workflow is:

```text
Owner request
   ↓
ORION freezes project + sandbox policy
   ↓
Coding model / Harness works inside disposable workspace
   ↓
tests / build / evidence
   ↓
ORION computes exact diff + receipts
   ↓
owner reviews/promotes bounded result
   ↓
approved changes enter real project
```

## Why

A sandbox can make many individual coding operations low-risk:

- creating/editing source files;
- running project tests;
- compiling/building;
- creating temporary artifacts;
- iterating after failures;
- using local development tools.

This is preferable to asking the owner to approve every ordinary edit or test.

The owner should approve the **boundary and promotion**, not each keystroke.

## Three risk zones

### GREEN — autonomous inside disposable workspace

May run without repeated owner confirmation after the task is authorized:

- read/write files under the assigned sandbox/worktree;
- create/delete temporary files inside that sandbox;
- run bounded build/test/lint commands;
- use already-installed development tools;
- inspect repository history and project files;
- retry failed tests;
- create candidate patches/diffs;
- generate evidence.

### YELLOW — explicit ORION policy or one bounded confirmation

Examples:

- package/dependency installation;
- network access;
- modifying lockfiles;
- invoking external cloud services;
- changing project configuration with effects beyond the sandbox;
- launching long-running background processes;
- touching project secrets or credential stores;
- publishing/pushing to a remote repository;
- writing outside the disposable workspace but still inside an approved project root.

These can later become pre-approved policies for known-safe registries/tools, but should not silently widen themselves.

### RED — never autonomous

Examples:

- Windows/system directories;
- boot configuration;
- registry/security policy;
- services/drivers;
- user credential stores;
- browser cookies/tokens;
- SSH/API keys;
- arbitrary files outside approved roots;
- deleting/moving unrelated user data;
- disabling antivirus/firewall/ORION controls;
- modifying ORION authority code/policy while executing an ordinary project task;
- changing STOP/approval enforcement;
- arbitrary external side effects such as sending messages, payments, account changes or deployments.

A model/harness cannot promote itself from GREEN/YELLOW into RED.

## Promotion gate

Sandbox success does not automatically mean host/project success.

Before changes are promoted:

1. identify exact changed files;
2. verify all paths remain in authorized scope;
3. compute hashes/diff;
4. run deterministic tests;
5. record evidence;
6. flag dependency/network/config changes separately;
7. require the owner or an already-approved promotion policy to accept the bounded diff;
8. apply through a deterministic ORION Hand.

The coding agent should never directly "graduate" its own sandbox changes into protected state.

## Downloads and network

A blanket "no downloads ever" is too restrictive for normal software development because dependencies and tool metadata may legitimately be required.

Instead ORION should default to **network denied** and support explicit egress policies such as:

- pre-approved package registries;
- pinned package/version downloads;
- source repository fetches;
- no arbitrary URLs;
- no credential-bearing requests unless separately authorized.

Downloaded artifacts remain untrusted until verified and confined.

## Sandbox strength

The sandbox is a risk-reduction layer, not the sole authority boundary.

DeepSeek Harness currently offers same-host Windows restriction mechanisms (restricted token / ACL style confinement). These are useful but must not be assumed equivalent to a VM security boundary.

For unattended agentic coding, ORION should benchmark at least two isolation tiers:

1. lightweight same-host sandbox/worktree for ordinary trusted development;
2. stronger disposable VM/container/Windows Sandbox/Hyper-V style environment for untrusted repositories, installers, native binaries or higher-risk agent loops.

The stronger tier should be preferred when arbitrary project code will execute.

## Required escape protections

ORION's scope checks must resolve real targets rather than trusting path strings.

At minimum guard against:

- `..` traversal;
- symlinks/junctions/reparse points;
- hard links where relevant;
- mounted/network paths;
- environment-variable expansion;
- alternate shells/interpreters;
- child/background processes;
- tools that can write indirectly;
- archive extraction path traversal;
- Git hooks;
- package install scripts;
- build scripts that escape the workspace.

No model claim can override these deterministic checks.

## STOP

STOP remains outside the sandbox and outside the agent.

It must be able to:

- cancel the active model request;
- stop the Harness/agent loop;
- terminate child/background process trees;
- prevent further promotion;
- leave the sandbox in inspectable state;
- report whether cleanup is complete or uncertain.

## Consequence for phone UX

This policy should drastically reduce remote interaction.

For a normal coding request the intended experience is:

```text
"Build/fix this feature in PayDay."
        ↓
ORION: sandboxed coding session started
        ↓
agent works, tests, retries
        ↓
ORION: ready for review
        ↓
one compact card:
  4 files changed
  tests PASS
  no network
  no protected paths
  [View diff] [Approve & apply]
```

The owner should not need to approve ordinary file edits or test commands one by one.

## Relationship to DeepSeek Harness

DeepSeek Harness becomes a stronger candidate under this model.

It may be allowed to behave agentically **inside** a bounded sandbox while ORION remains responsible for:

- sandbox creation;
- tool restriction;
- network policy;
- protected-path enforcement;
- resource/time/turn budgets;
- STOP;
- exact diff/evidence;
- promotion to real project state.

This is the preferred first benchmark shape for Harness.

## Non-decision

This document does not declare the current Harness sandbox secure enough for unattended coding.

That requires physical adversarial tests, including path escapes, junctions, package install scripts, child processes, background jobs, network denial, STOP and promotion-gate enforcement.
