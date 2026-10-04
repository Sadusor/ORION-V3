# ORION Agent / Security Donor Analysis

Date: 2026-10-04  
Status: ANALYTICAL REFERENCE  
Purpose: preserve donor findings so later implementation does not depend on chat memory

## Executive conclusion

ORION should not search for one repository that replaces its architecture.

The strongest pattern emerging from the donor set is compositional:

```text
ORION authority
  ├─ deterministic Hands
  ├─ minimal ORION Agent loop
  ├─ qualified Skills
  ├─ sandbox boundary
  ├─ runtime Security Plane
  ├─ Memory / provenance
  └─ external specialist agents only where useful
```

Different repositories are strongest at different layers.

The recommended design principle is:

**borrow capabilities and verified mechanisms; do not import donor authority models wholesale.**

---

## 1. Google Mantis — highest-value coding-security donor

Fork:

`Sadusor/mantis`

Upstream:

`google/mantis`

Reviewed fork head on 2026-10-04:

`f48a85e8823ee6f4824ae9a24b9b2efb8aab8c9a`

License:

Apache-2.0

### What Mantis is

Mantis is a modular security-review toolkit plus an ADK reference harness for coding agents.

Its pipeline includes:

- repository history analysis;
- structural indexing;
- architecture/KB synthesis;
- threat modeling;
- planning;
- vulnerability research;
- deduplication;
- review/validation;
- production-viability critique;
- vulnerability reproduction;
- exploit chaining;
- patching;
- risk calibration;
- reflection/learning;
- final report generation;
- developer security advice.

This is not merely a scanner.

It contains reusable security skills, state contracts, sandbox environments, budgets, evidence mechanisms and deterministic orchestration guidance.

### Most important architectural fit

Mantis explicitly recommends deterministic orchestration rather than letting the LLM control the pipeline.

Its `mantis-pipeline-adapter` guidance says:

- programmatic harness controls flow;
- structured filesystem/database state is the source of truth;
- model outputs should remain compact and structured;
- routine deterministic manipulation should be implemented as tools;
- expensive models should be used only where empirically justified.

This matches ORION's doctrine unusually closely.

### Snapshot model

Mantis has one of the best donor patterns for avoiding stale analysis.

A pass may pin one immutable snapshot.

Identity ladder includes:

- clean VCS → commit hash;
- dirty VCS → commit + content hash;
- no VCS → content hash;
- binary → artifact hash;
- uncopyable/live target → degraded unpinned state.

Findings are bound to the snapshot where they were produced.

Trusting decisions only proceed when the finding's discovery snapshot matches the active snapshot.

Implication for ORION Agent:

A model proposal should be bound to relevant task/workspace state.

A changed state invalidates the proposal rather than silently executing it.

### Read-only target / private shadow pattern

Mantis separates:

- source snapshot for authoritative reads;
- private mutable shadow for build/reproduction/patch work.

That maps directly to ORION sandbox-first coding.

ORION can preserve:

```text
REAL PROJECT / FROZEN SNAPSHOT
          read only
             ↓
       PRIVATE SHADOW
        agent edits
        tests/builds
             ↓
      candidate diff
             ↓
       ORION promotion
```

### Reproduce → patch → re-attack

Mantis does not accept "patch applied" as proof.

Its security workflow separates patch creation from independent re-attack.

That is highly relevant to ORION cloud coding:

```text
coder proposes patch
     ↓
sandbox tests
     ↓
independent security/re-attack lane
     ↓
deterministic evidence
     ↓
promotion candidate
```

The patch author should not be the only evaluator of its own fix.

### Sandbox tiers

Mantis supports multiple environments:

- static-only;
- microsandbox;
- gVisor;
- GCE sandbox.

The stronger GCE environment includes active isolation checks.

It probes whether the guest unexpectedly has:

- metadata/IAM token access;
- direct IPv4 egress;
- public DNS;
- Google API connectivity;
- IPv6 egress;
- public UDP DNS.

The lesson for ORION is critical:

**do not infer isolation from configuration. Prove isolation from inside the guest.**

### Host boundary

Mantis's documented invariant separates host target access from guest mutation.

This should influence ORION's coding security contract:

- model/agent gets no direct protected-host mutation capability;
- target paths are canonicalized;
- code snapshot and sandbox state have distinct roots;
- sandbox outputs return through a narrow promotion gate.

### Mantis Advise

`mantis-advise` is especially relevant to future ORION Skills/Memory integration.

It can provide a coding agent with:

- active threat boundaries;
- historical vulnerabilities;
- verified patch patterns;
- known false positives;
- learned security invariants;
- recurrence/lineage context.

Potential future ORION integration:

```text
owner asks for feature
      ↓
ORION resolves target
      ↓
Security Advisor queries Mantis-derived knowledge
      ↓
small security context packet
      ↓
coding model / ORION Agent
      ↓
post-change targeted Mantis review
```

This keeps security knowledge as context while ORION keeps authority.

### What not to adopt directly

Do not make Mantis's full multi-stage campaign graph the default ORION agent loop.

Do not assume its cloud/GCE options are free or required.

Do not make Mantis's own agent harness authoritative over ORION tasks.

Use skills, isolation tests, snapshot ideas, security state and verification patterns selectively.

---

## 2. DeepSeek Harness — mature full-agent competitor/donor

Fork:

`Sadusor/deepseek-harness`

Reviewed upstream snapshot:

`5badb15009ae1756c3afe0ae0cef1faafc290ccc`

### Strengths

- real agent loop;
- typed tool registry;
- scoped tool restriction;
- monotonic guard seam;
- shell/filesystem tooling;
- background jobs;
- subagents;
- persistent sessions;
- browser/computer-use providers;
- headless JSON runner;
- model/provider routing;
- explicit tool outcome semantics.

### Most useful donor patterns

- monotonic deny;
- machine-readable event stream;
- `OUTCOME_UNKNOWN`;
- lifecycle/cancellation ideas;
- headless runner;
- tool registry structure;
- provider-neutral model adapter.

### Main mismatch

It duplicates boundaries ORION already owns:

- task/session lifecycle;
- approval service;
- tool registry;
- sandbox;
- permissions.

Deep integration risks two sources of truth.

Therefore DeepSeek Harness remains:

- donor;
- benchmark competitor;
- possible specialist/fallback substrate.

### Security posture

Do not rely on Harness's own same-host sandbox as the outer security boundary.

Initial benchmark should use:

- headless profile;
- no Web/Desktop control plane;
- no PTC/run_code;
- outer ORION-controlled disposable isolation;
- bounded tool set;
- explicit time/step budget;
- no host credentials.

---

## 3. ButterClaw — runtime Security Plane donor

Fork:

`Sadusor/butterclaw`

Upstream:

`butterclaw-tech/butterclaw`

License:

Apache-2.0

### Useful implemented patterns

Source review found:

- deterministic `pre_brain`, `post_brain`, `pre_tool` policy stages;
- positive capability matrix;
- fail-closed when capability data is missing;
- per-tool scope requirements;
- policy event log;
- bounded chain semantics;
- process lineage/quarantine concepts;
- transport payload constraints;
- live-fire/adversarial test scripts.

### ORION mapping

Potential ORION Security Plane:

```text
PRE-MODEL
  cheap deterministic input checks

MODEL
  untrusted reasoning

POST-MODEL
  normalize/inspect output

PRE-TOOL
  exact ORION capability/scope decision

RUNTIME
  process/network/sandbox monitoring

POST-EXECUTION
  evidence + independent verification
```

### Caveat

Prompt-injection regex/signature detection is not a strong authority boundary.

Attackers can obfuscate content and models can fail in novel ways.

Use static signatures as:

- cheap early filter;
- telemetry;
- defense in depth.

The true boundary remains:

- capability allowlist;
- canonical scope check;
- sandbox;
- process/network isolation;
- promotion gate.

---

## 4. Google mcp-security — security tool contract / external integration donor

Fork:

`Sadusor/mcp-security`

Upstream:

`google/mcp-security`

License:

Apache-2.0

### Repository role

Provides MCP servers for Google security products such as:

- Security Operations;
- SOAR;
- Threat Intelligence;
- Security Command Center.

Also contains an ADK autonomous SOC example.

### ORION value

Main value now is contract/reference design, not runtime dependency.

Potential future ORION Security capabilities:

- inspect file/hash;
- inspect process;
- inspect connection;
- inspect downloaded artifact;
- inspect dependency;
- query threat intelligence;
- return provenance-backed security evidence.

### Constraint

Do not make cloud security products part of ORION's base safety.

No surprise paid usage.

External security services must remain optional connectors.

---

## 5. Athena Investigation MCP Server — narrow-capability donor

Fork:

`Sadusor/athena-investigation-mcp-server`

Upstream:

`brunofreitas-br/athena-investigation-mcp-server`

License:

MIT

### Important pattern

It intentionally does not expose arbitrary SQL.

It exposes a tiny fixed investigation surface with:

- validated inputs;
- parameterized backend calls;
- server-side result limits;
- timeout;
- provenance/query metadata;
- read-only semantics.

### ORION lesson

A safe Hand/Skill should expose the smallest operation needed.

Prefer:

```text
search_project_symbol(name)
run_named_test(test_id)
inspect_dependency(name)
publish_exact_artifact(...)
```

over:

```text
execute_shell(anything)
execute_sql(anything)
run_python(anything)
```

Generic interpreters belong inside strong disposable boundaries, not as default production capabilities.

---

## 6. AgenticAnomaly — adversarial benchmark donor

Purpose:

indirect prompt-injection CTF for agentic SOC workflows.

ORION use:

- hostile README;
- malicious log/event text;
- tool-output injection;
- false-positive/false-negative measurement;
- repeat stochastic attacks across several runs.

It should influence benchmark fixtures, not production authority.

---

## 7. AutoHarness — governance/test donor

Useful concepts:

- risk classification;
- governance pipeline;
- resource budgets;
- cost attribution;
- audit;
- evaluation.

Do not insert it as another authority layer.

---

## 8. CLI-Anything — deterministic specialist Hand donor

Role:

preferred narrow executor when supported application behavior can be represented deterministically.

Execution hierarchy remains:

```text
native deterministic Hand
  ↓
specialist CLI/API Hand
  ↓
ORION Agent
  ↓
external full agent
```

---

## 9. OpenHands — tool implementation donor

Useful:

- file/editor tool interfaces;
- terminal abstractions;
- execution event patterns.

Do not assume its agent runtime is needed.

Previous ORION/OpenHands experiment also demonstrated the importance of explicit tool registration: the initial path produced zero ActionEvents because default tools had not been registered.

---

## 10. Octop — workspace/multi-lane/UI donor

Useful:

- multiple agents/workspaces;
- project vs personal separation;
- background-work presentation;
- remote desktop/channel patterns;
- ACP-style delegation.

Do not use as authority.

---

## 11. openmuse — transaction/evidence donor

Useful:

- proposal hash;
- stale proposal rejection;
- operation identity;
- idempotency;
- outcome-unknown semantics;
- receipts.

These principles are already entering Agent V0.

---

## 12. Memory donors

### OpenViking

Useful hierarchical resource/memory/skill representation and L0/L1/L2 retrieval inspiration.

### TencentDB Agent Memory

Useful separation of chat/skills/wiki/code graph and on-demand context.

### agentmemory

Useful hybrid/vector/graph/temporal/consolidation concepts.

### Aider / Serena

Useful compact code context and symbol-aware retrieval.

ORION Memory remains provenance-backed context, never authority.

---

## 13. KIRA

Useful for:

- endpoint/router patterns;
- voice lease;
- local Qwen vision precedent;
- device/channel ideas.

KIRA evidence can guide ORION qualification but does not automatically transfer proof.

---

## 14. New composite architecture

The donor research supports:

```text
                           OWNER
                             ↓
                      PHONE / UI
                             ↓
                        ORION CORE
          ┌──────────────────┼──────────────────┐
          │                  │                  │
       MEMORY             AUTHORITY          SECURITY
          │                  │                  │
          │           task/scope/policy    cheap guards
          │           capability leases    process watch
          │           STOP / evidence      isolation checks
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ↓
                           ROUTER
                ┌────────────┼────────────┐
                ↓            ↓            ↓
          DIRECT HAND    WORKFLOW      AGENT V0
                │          / SKILL          │
                └────────────┼──────────────┘
                             ↓
                       OUTER SANDBOX
                             ↓
                   BUILD / TEST / VERIFY
                             ↓
                       MANTIS SECURITY
                      review / re-attack
                             ↓
                      PROMOTION GATE
                             ↓
                         REAL PROJECT
```

External full agents remain optional workers inside the same outer boundary.

---

## 15. What should remain stable while building

Do not modify:

- frozen legacy Remote UI;
- frozen Android baseline;
- proven Capability Registry semantics;
- known-good Remote exact-SHA path;
- Memory authority semantics;
- STOP authority;
- owner approval semantics.

Agent V0 is additive.

---

## 16. Future implementation placeholders

The code should make room for, but not implement prematurely:

### MemoryContextProvider

Later injects small provenance-backed context packets.

### SkillProvider

Later exposes only ORION-qualified versioned Skills.

### SecurityAdvisor

Later integrates Mantis-derived advice, ButterClaw-style runtime signals, optional threat intelligence.

### SandboxProvider

Later creates lightweight worktree or strong VM/container boundaries.

### EscalationProvider

Later routes to:

- Qwen THINKING;
- larger local model;
- cloud reviewer/coder;
- owner.

These providers cannot alter ORION authority semantics.

---

## 17. Benchmark philosophy

The benchmark should answer architectural questions, not reward feature count.

A/B/C:

- A = direct deterministic Hands;
- B = ORION Agent V0;
- C = DeepSeek Harness.

Hard safety failures are disqualifying.

Among safe candidates compare:

- completion correctness;
- hidden tests;
- recovery from wrong hypotheses;
- latency;
- model turns/tokens;
- tool calls;
- CPU/GPU/VRAM/RAM;
- maintenance complexity.

A richer framework does not win by default.

---

## 18. Post-benchmark rule

Do not pre-commit to Agent V1.

After the benchmark:

1. inspect physical evidence;
2. identify where the loop helped or hurt;
3. identify whether Harness solved anything materially better;
4. identify whether Mantis/ButterClaw security components should move earlier;
5. owner and assistant brainstorm next direction from evidence.

That discussion intentionally remains open.
