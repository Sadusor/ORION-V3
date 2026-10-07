# ORION V3 — Autonomous Work Loop V1 Donor Code Acquisition Audit

Date: 2026-10-07  
Status: **TOMORROW-READY / REUSE-FIRST / NO RUNTIME CHANGES**  
Priority: **Autonomous Work Loop V1 Step 0**

## Purpose

This is not a donor wishlist. It records the concrete source files/patterns we should inspect, benchmark, adapt or reject before writing Autonomous Work Loop code.

Rule:

```text
ORION existing code
  -> TheHands existing code
  -> exact audited donor code
  -> only then new code
```

Donors never become ORION authority.

## Executive decision

The first implementation should remain tiny:

```text
STATE -> local model -> ORION policy -> confined Hand -> authenticated evidence -> STATE
```

The most important unresolved technical dependency is **Windows-native Work Hand confinement**.

### New top confinement candidate

**Anthropic Sandbox Runtime (SRT)** — https://github.com/anthropics/sandbox-runtime  
License: Apache-2.0. Windows support is explicitly alpha.

Why it is now candidate #1 for physical evaluation:
- native Windows path; no WSL/container required;
- dedicated `srt-sandbox` local account;
- write access deny-by-default outside explicit `filesystem.allowWrite`;
- NTFS explicit ACEs for allowed/denied paths;
- Windows Filtering Platform (WFP) egress fence keyed to sandbox account SID;
- child process tree inherits the sandbox identity;
- session cleanup removes ACEs added by the session;
- network can be domain allowlisted;
- source exposes a library/CLI wrapper rather than requiring its own agent architecture.

Exact code to inspect:
- `src/sandbox/sandbox-config.ts` — policy schema, filesystem/network semantics, path validation.
- Windows implementation under the packaged `vendor/srt-win` source/binary build path — account/ACL/WFP execution boundary.
- tests covering Windows filesystem/network enforcement.
- `package.json` — Apache-2.0 and build/runtime dependencies.

ORION use:
- **do not fork its agent behavior**; there is none to import.
- prototype a narrow `WorkHandSandboxAdapter` that launches an already-authorized TheHands operation through SRT.
- ORION supplies workspace path and network policy.
- SRT supplies OS enforcement.
- TheHands still supplies operation execution/evidence.
- ORION still owns authorization, STOP, GREEN/YELLOW/RED and PASS.

Required physical attacks before adoption:
1. write inside workspace succeeds;
2. create/overwrite/delete outside workspace fails;
3. path traversal fails;
4. symlink/junction/reparse escape fails;
5. rename/move escape fails;
6. child PowerShell/Python/cmd inherits restrictions;
7. temp/profile/AppData writes are understood and bounded;
8. Git works without opening dangerous host paths;
9. network is denied when disabled;
10. allowed network destinations work only when explicitly enabled;
11. STOP kills the owned run;
12. crash/reset does not leave dangerous ACL grants behind.

Do not qualify SRT from README claims alone.

## Confinement challenger #2 — OpenAI Codex Windows sandbox

Repository: https://github.com/openai/codex  
License: Apache-2.0.

Exact code worth studying:
- `codex-rs/windows-sandbox-rs/sandbox_smoketests.py`
- `codex-rs/sandboxing/src/windows.rs`
- `codex-rs/core/src/windows_sandbox.rs`
- related `windows-sandbox-rs` token/ACL implementation.

What to reuse first:
- **the smoke-test/attack matrix**, even if we do not reuse the runtime.
- fail-closed policy compatibility logic.
- Windows path normalization and writable-root/read-only-carveout ideas.

The smoke suite already tests the exact semantic we need:
- read-only cannot write;
- workspace-write can write in workspace;
- workspace-write cannot write outside;
- additional roots are explicit;
- Python child writes obey policy;
- network denial is tested.

Why it is not candidate #1:
2026 public issues show real Windows edge cases including DACL allocation failures, workspace-write becoming read-only, outside-workspace mutation reports in elevated configurations, persistent ACL mutation and concurrent capability/ACL races. Therefore: **excellent donor/test source, not trusted runtime until physically disproven on our PC**.

## Existing donor code — exact acquisition map

### 1. TheHands — KEEP as execution/evidence substrate

Repository: `Sadusor/TheHands-`

Use:
- existing remote execution path;
- existing GitHub evidence publication to `thehands-results`;
- existing STOP/runner behavior where applicable;
- inspect current path/scope validation before adding any confinement layer.

Do not modify frozen proven TheHands core merely to fit the Work Loop.

Tomorrow audit must locate exact current files/functions for:
- command dispatch;
- PowerShell Hand;
- working-directory binding;
- allowed/denied path checks;
- process ownership/termination;
- evidence JSON creation/publication;
- result typing.

If existing scope enforcement already gives a hard workspace boundary, prove it before adding SRT.

### 2. OpenMuse — proposal identity / stale approval / execution receipt

Repository: `Sadusor/openmuse`

Exact file:
- `apps/server/src/actions.ts`

Concrete code/patterns to adapt:
- SHA-256 proposal hash over the exact prepared action;
- idempotency key -> stable operation identity;
- proposal expiration;
- approve/deny binds to the exact hash;
- changed/stale proposal cannot reuse approval;
- claim before execute;
- distinguish `failed` from `outcome_unknown`;
- append activity/receipt after execution.

ORION adaptation:
- GREEN may auto-authorize, YELLOW requires owner approval, RED never reaches execution.
- authorization token binds project/task/proposal hash/scope.
- never copy Google-specific action types or OpenMuse ownership model.

Exact second file:
- `apps/server/src/jev/service.ts`

Reuse only:
- compare-and-swap / generation semantics that reject superseded decisions.
Useful later for Work Chat owner choices and Council panels, not needed to start the tiny loop.

### 3. CLI-Anything — deterministic Hand contract

Repository: `Sadusor/CLI-Anything`

Exact reference:
- `cli-anything-plugin/HARNESS.md`
- specific harnesses only after Step-0 identifies an operation we need.

Patterns to adapt:
- inspect before mutate;
- one logical operation per command;
- real backend invocation;
- `--json` machine output;
- explicit return codes;
- session state only where genuinely needed;
- verify the final artifact rather than trusting process exit;
- immutable preview/evidence bundles where relevant;
- append-only trajectory pattern.

ORION adaptation:
```text
AuthorizedOperation
  -> deterministic adapter
  -> real backend
  -> machine receipt
  -> verifier
```

Do not import CLI-Anything's whole harness framework into the first loop.

### 4. OpenJarvis — path validation now; Skills later

Repository: `Sadusor/OpenJarvis`

Exact file available now:
- `src/openjarvis/sandbox/mount_security.py`
  - `AllowedRoot`
  - `MountAllowlist`
  - `load_mount_allowlist()`
  - `validate_mount()`
  - `validate_mounts()`
  - `DEFAULT_BLOCKED_PATTERNS`

Useful behavior:
- resolve/normalize path before checking;
- require path under configured root;
- reject sensitive path components/patterns;
- block credentials/configs.

Important caveat:
- empty roots currently means allow all non-blocked paths. ORION must be **fail closed**, so never inherit that default.

Use now:
- path-normalization/allowlist ideas for ORION pre-execution policy and sandbox mount validation.

Use later:
- registries;
- SkillManager/SkillTool/SkillExecutor patterns;
- capability declarations;
- dependency cycle/depth checks;
- skill trust tiers;
- event adapters.

Do not use:
- OpenJarvis agent loop as ORION authority;
- default-allow security configuration;
- discovered skill as automatically trusted.

### 5. Aider repo-map — first lightweight code-context baseline

Repository: `Sadusor/aider`

Exact file:
- `aider/repomap.py`

Concrete reusable ideas:
- tree-sitter definitions/references;
- ranked symbol/file map;
- token-bounded repo context;
- cache keyed by file modification;
- focus ranking from mentioned files/identifiers.

Use:
- benchmark as the **smallest code-search/context Skill** before adopting a larger graph system.

Do not use Aider editing authority.

### 6. Graft — stronger code-context challenger

Repository: `Sadusor/Graft`

Concrete commands/capabilities to benchmark against Aider:
- `graft build` — deterministic tree-sitter graph;
- `graft ask --json`;
- `graft skeleton`;
- `graft callers`;
- `graft grep`;
- `graft map`;
- `graft blast`;
- `graft check --json`.

Strong ORION fit:
- structural layer is local/deterministic/no model;
- machine-readable queries;
- freshness check;
- blast-radius query after edits.

Caution:
- `graft init` can write user-level agent configuration; **do not run it blindly**.
- telemetry/version behavior must be disabled/reviewed for ORION qualification.
- deep LLM layer is not required for V1.

Decision:
Aider = minimal baseline.
Graft = benchmark challenger. Adopt only if measured context quality/latency justifies extra dependency.

### 7. OpenSandbox — container isolation challenger

Repository: `Sadusor/OpenSandbox`

Exact useful surfaces:
- server storage config `allowed_host_paths`;
- host volume API with read-only/read-write mounts;
- command/file APIs;
- egress policy APIs.

Use only if native Windows SRT/TheHands mechanisms are insufficient or if we later want disposable container workspaces.

Do not import Kubernetes/control-plane complexity into V1.

### 8. KnowledgeOS — evidence semantics, not another evidence store

Repository: `Sadusor/KnowledgeOS`

Reuse pattern:
- evidence is factual observation;
- interpretation is separate;
- provenance/trace belongs with retrieval/evidence.

Use to shape ORION verifier/receipt fields.
Do not create a second canonical evidence database.

## External research — additional donor candidates

### A. Anthropic Sandbox Runtime — **NEW / HIGH PRIORITY**

Repository: https://github.com/anthropics/sandbox-runtime  
License: Apache-2.0.  
Disposition: **benchmark first for Windows Work Hand confinement**.

This is the most directly aligned new donor found in the 2026 research.

### B. OpenAI Codex Windows sandbox — **NEW / HIGH-VALUE TEST DONOR**

Repository: https://github.com/openai/codex  
License: Apache-2.0.  
Disposition: **reuse attack tests/policy ideas; runtime challenger only**.

### C. agent-win-sandbox — **NEW / REFERENCE**

Repository: https://github.com/fmuecke/agent-win-sandbox

Useful:
- dedicated standard Windows user;
- independent logon/noninteractive desktop;
- fixed workspace;
- firewall/broker/setup/checker patterns.

Author explicitly says it reduces blast radius and is **not hard containment**.
Disposition: reference/fallback only, not sufficient by itself for our hard confinement gate.

### D. Anthropic Agent Skills repository — **LATER RESEARCH SOURCE**

Repository: https://github.com/anthropics/skills

Useful only when Milestone 8 starts. Do not import community skills into V1 before qualification rules exist.

### E. Nanobrowser — **LATER browser Hand challenger**

Repository: https://github.com/nanobrowser/nanobrowser  
License: Apache-2.0.

Potential later use:
- browser navigation/DOM operation;
- local/BYOK provider model;
- planner/navigator/validator separation ideas.

Not relevant to the core filesystem loop. Do not distract Step 0 with it.

### F. nono-agent-sandbox — **NOT CURRENT WINDOWS DONOR**

Repository: https://github.com/syntax-syndicate/nono-agent-sandbox  
License: Apache-2.0.

Interesting capability/audit ideas, but its own roadmap says Windows support is future work. Do not use for tomorrow's Windows confinement decision.

## Code we should actually plan to adapt vs merely study

### Likely direct/narrow adaptation

1. OpenMuse `actions.ts`
   - proposal hashing;
   - idempotency;
   - stale approval rejection;
   - outcome_unknown distinction.

2. OpenJarvis `mount_security.py`
   - path resolve/normalize;
   - allowed-root check;
   - blocked sensitive path patterns;
   - changed to fail-closed semantics under ORION.

3. CLI-Anything harness patterns
   - typed operation -> JSON receipt -> final artifact verification.

4. Aider `repomap.py` OR Graft deterministic graph
   - only after core loop, as first repo-context Skill.

### Prefer wrapping as external dependency first

5. Anthropic Sandbox Runtime
   - do **not** copy hundreds of lines of Windows ACL/WFP code into ORION initially.
   - first benchmark/wrap its CLI/library behind a tiny ORION adapter.
   - copy/adapt only if qualification, maintenance and packaging justify ownership later.

### Reuse tests/attack cases even if runtime rejected

6. Codex `sandbox_smoketests.py`
   - convert relevant cases into ORION's sandbox qualification suite.
   - add junction/reparse/path traversal/rename/temp/profile/process-tree/STOP attacks.

## Tomorrow: exact Step-0 execution order

1. **Audit TheHands first.**
   Locate exact dispatcher, cwd/scope, path checks, process lifecycle and evidence publisher.
2. **Audit ORION-V3 existing seams.**
   Locate current Qwen/provider call, STOP, policy/freeze rules, project state/status/event interfaces.
3. Produce a table for each tiny-loop requirement:
   `EXISTS / PARTIAL / MISSING / REUSE`.
4. **Confinement spike A: Anthropic SRT.**
   No integration yet. Run a disposable physical workspace attack suite.
5. **Confinement spike B only if needed: Codex/OpenJarvis/OpenSandbox patterns.**
6. Choose the smallest confinement mechanism by physical evidence.
7. Only then write Minimal Vault + tiny loop.
8. Do not touch Memory V1/V1.1 or frozen TheHands core.

## Sandbox qualification suite to borrow/build

Minimum:
- allowed write inside workspace;
- denied create/write/delete outside;
- denied relative `..\` escape;
- denied absolute-path escape;
- denied symlink/junction/reparse escape;
- denied rename/move outside;
- child cmd/PowerShell/Python inherits boundary;
- Git normal operations inside workspace;
- protected `.git/hooks` / config behavior explicitly decided;
- temp/profile/AppData behavior measured;
- credentials paths unreadable where required;
- network off means actual socket/HTTP denial;
- optional allowlisted network only reaches approved destination;
- concurrent runs do not widen each other's access;
- crash cleanup does not leave grants;
- ORION STOP kills the owned process tree;
- evidence proves each attack result.

## Reuse acceptance criteria

A donor component is accepted only if:
1. license permits intended use;
2. exact code path is identified;
3. it solves a current missing capability;
4. ORION remains authority;
5. it is replaceable behind a narrow adapter;
6. security defaults are fail-closed or overridden fail-closed;
7. physical Windows test passes where relevant;
8. it does not mutate frozen Memory/TheHands;
9. resource/idle cost is acceptable;
10. its failure is represented truthfully, not converted into PASS.

## Things explicitly deferred

- polished Work UI;
- Council framework;
- notification taxonomy;
- generic workflow DSL;
- automatic skill marketplace;
- deep code graph if Aider baseline is enough;
- container/Kubernetes control plane;
- browser automation;
- self-development.

## Bottom line

Tomorrow's most valuable question is no longer "how do we design the Work Loop?"

It is:

> **What exact existing ORION/TheHands seams can we reuse, and can Anthropic SRT (or a smaller existing mechanism) physically confine TheHands to one Windows workspace without breaking our fast low-consumption workflow?**

If yes, the largest safety unknown in the minimal loop is removed and implementation can stay small.
