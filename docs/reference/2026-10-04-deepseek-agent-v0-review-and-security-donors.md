# DeepSeek ORION Agent V0 Review + Security Donor Follow-up

Date: 2026-10-04  
Status: REVIEWED / CLOUD COUNCIL STILL PENDING  
Execution authorization: NONE IMPLIED

## DeepSeek verdict

DeepSeek returned:

**BUILD ORION AGENT V0**

Its central argument:

- ORION already owns the hard authority-plane components;
- the missing piece can remain a small bounded model -> proposal -> policy -> Hand -> observation loop;
- DeepSeek Harness should remain a donor/benchmark competitor rather than become ORION's authority/runtime center;
- the main engineering risk is scope creep.

## Strong recommendations accepted for evaluation

Candidate Agent V0 should remain deliberately narrow:

- one model;
- one active action at a time;
- structured proposal only;
- static task-scoped tool registry;
- deterministic policy gate;
- normalized observations;
- append-only journal;
- explicit budgets;
- externally owned STOP;
- no subagents;
- no background-job semantics;
- no model-written workflows;
- no `run_code`;
- no parallel tool execution;
- no self-registration;
- no Skills in V0;
- no mid-loop memory retrieval in the benchmark.

DeepSeek proposed an A/B/C comparison:

A. Qwen -> deterministic ORION Hands  
B. same Qwen -> minimal ORION Agent -> same Hands  
C. same Qwen -> DeepSeek Harness -> ORION guard -> same Hands

This is directionally accepted as the benchmark shape.

## Required corrections before implementation

### Model confidence is not authority

A model's self-reported `confidence` may be recorded for telemetry/routing, but it must not authorize an otherwise denied operation.

Security approval remains deterministic.

### Canonical target before policy

The policy gate must authorize the resolved canonical target, not the model-provided path string.

Qualification must cover:

- `..` traversal;
- symlinks/junctions/reparse points;
- alternate path spellings;
- environment-variable expansion;
- mounted/network targets where relevant.

### OUTCOME_UNKNOWN is not equivalent to timeout

A timeout alone does not automatically mean OUTCOME_UNKNOWN.

The executor should distinguish:

- process definitely never started;
- process started and was definitely terminated before a side effect;
- side effect committed;
- side effect state cannot be determined.

Only the last case is OUTCOME_UNKNOWN.

### Benchmark sentinel

Any System32/path-escape probe must run only in an external disposable VM/sandbox.

Prefer an ordinary harmless outside-workspace sentinel for initial development tests.

Protected-system-path probes are later adversarial tests inside a disposable environment, never host tests.

### Stale-state binding

Before execution, the proposal/operation should bind to the relevant workspace/task state hash.

A workspace mutation that changes the assumptions of the proposal invalidates it.

### STOP on Windows

For Windows qualification, STOP must physically prove full process-tree containment/cleanup, preferably using a supervisor/Job Object or equivalently strong process ownership rather than relying only on cooperative cancellation.

## New security forks

Owner forked:

- `Sadusor/butterclaw` from `butterclaw-tech/butterclaw` — Apache-2.0
- `Sadusor/mcp-security` from `google/mcp-security` — Apache-2.0
- `Sadusor/athena-investigation-mcp-server` from `brunofreitas-br/athena-investigation-mcp-server` — MIT

### ButterClaw

Highest immediate security-donor value.

Useful patterns confirmed in source:

- positive capability matrix;
- strict fail-closed behavior if capability metadata is absent;
- pre-brain / post-brain / pre-tool deterministic policy stages;
- policy event audit;
- bounded chain semantics;
- process-lineage/quarantine ideas;
- STDIO payload constraints;
- adversarial/live-fire testing.

ORION should borrow design/tests selectively, not install ButterClaw as authority.

Static prompt/signature detection is defense-in-depth only. It cannot replace deterministic capability enforcement or sandbox isolation.

### Google mcp-security

Useful primarily as a security-capability/tool-contract reference, not as ORION's base security dependency.

Potential later ORION Security Sentinel capabilities may expose narrow operations such as:

- inspect file/hash;
- inspect process;
- inspect connection;
- inspect dependency/download;
- query threat intelligence;
- produce provenance-backed security evidence.

Paid Google SecOps/SOAR/SCC services are optional external integrations, not required for ORION safety.

### Athena Investigation MCP Server

Useful narrow-capability donor.

Important pattern:

do not expose arbitrary backend power (for example arbitrary SQL) when a smaller typed capability can satisfy the task.

This reinforces ORION's Hand/Skill rule:

**publish bounded capabilities, not generic privileged interpreters.**

## Cloud council status

The first ORION Agent V0 cloud-council Remote run failed before contacting any provider because the probe required at least two configured-free reviewers and discovered fewer than two.

No unknown-cost provider was called.

The probe has been revised so **one configured-free cloud reviewer is sufficient**.

The updated review packet also includes the three new security donors.

## Current recommendation

Do not start a large agent framework.

Next sequence:

1. obtain at least one independent configured-free cloud review if available;
2. freeze the V0 contract;
3. build only the minimum loop slices;
4. qualify its security plane with donor-informed adversarial tests;
5. run A/B/C benchmark;
6. promote or reject Agent V0 based on physical evidence.

Do not let security-donor research delay the new UI indefinitely; Agent V0 and security contracts should remain bounded and modular.
