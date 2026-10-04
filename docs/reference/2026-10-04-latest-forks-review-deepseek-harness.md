# Latest Forks Review — DeepSeek Harness and New Donors

Date: 2026-10-04  
Status: REVIEWED / NO INSTALL OR EXECUTION AUTHORIZED

## Repositories reviewed

Forks created on or after 2026-10-03:

- `Sadusor/deepseek-harness` — upstream `deepseek-ai/deepseek-harness`
- `Sadusor/AutoHarness` — upstream `aiming-lab/AutoHarness`
- `Sadusor/CLI-Anything` — upstream `HKUDS/CLI-Anything`
- `Sadusor/mimic` — upstream `littledivy/mimic`
- `Sadusor/Octop` — upstream `TencentCloud/Octop`
- `Sadusor/openmuse`
- `Sadusor/GhostTrack`

DeepSeek Harness fork was pinned during review at:

`5badb15009ae1756c3afe0ae0cef1faafc290ccc`

Upstream release message: `0.2.1-alpha.1`.

## DeepSeek Harness — verdict

**Yes: this is a real full agent harness, and it is the strongest newly discovered full-agent candidate for ORION's later agent tournament.**

It is not merely a model wrapper.

The repository includes:

- a persistent agent loop;
- model/tool turn iteration;
- typed tool registry;
- PowerShell/Bash execution;
- filesystem read/write/edit/search;
- background jobs;
- persistent sessions;
- subagents;
- model-authored workflows;
- browser-use providers;
- computer-use providers;
- user approval;
- per-agent tool restrictions;
- sandbox policies including Windows support;
- headless one-shot execution;
- Web/Desktop/SDK/ACP surfaces;
- model/provider routing;
- plugin hot composition.

Its `headless` profile can run a single task as a coding agent and emit a JSON event stream, which is particularly suitable for an ORION benchmark wrapper.

## Why DeepSeek Harness fits ORION unusually well

### 1. Monotonic tool guard seam

`ctx.tools.guard()` runs after the extensible pre-execute stage.

A guard denial is monotonic: a later listener cannot turn the denied call back into permission.

This is a strong potential attachment point for an ORION lease/hash/scope guard.

ORION could therefore keep authority outside the agent:

`model -> DeepSeek agent loop -> ORION guard -> tool execution`

rather than trusting the agent's own approval logic.

### 2. Per-agent tool restriction

`ctx.tools.restrict(filter)` can narrow the global tool set for one agent.

That maps well to ORION's bounded-capability leases.

A benchmark agent can be exposed only to the exact tools needed for a disposable task.

### 3. Windows-specific execution support

The base composition includes PowerShell on Windows and a Windows restricted-token / ACL sandbox path.

This is directly relevant to the owner's Windows machine.

### 4. Useful failure semantics

The agent loop explicitly distinguishes:

- call never started;
- call started but outcome unknown;
- committed tool result;
- aborted before dispatch.

It does not automatically retry uncertain side effects.

This matches lessons ORION already adopted from openmuse-style outcome handling.

### 5. Headless machine-readable runner

`dsh --profile headless "<task>"`:

- runs one agent task;
- opens no server;
- can emit newline-delimited JSON;
- has resumable session identity;
- returns process exit status;
- exposes tool calls/results/status events.

This is much easier to benchmark deterministically than driving a GUI agent.

### 6. Local/self-hosted model route is architecturally possible

`dsh-llm-pi-ai` supports:

- multiple providers;
- hand-declared OpenAI-compatible gateways;
- self-hosted servers;
- custom model catalogs;
- selectable reasoning levels.

Ollama exposes an OpenAI-compatible local endpoint, so a local Qwen -> DSH experiment is technically plausible.

This is **not yet physically proven with `qwen35-9b-orion`** and must be qualified before being treated as a working ORION path.

## Why DeepSeek Harness must NOT replace ORION authority

The repository's own safety notice says it is developer-preview software, unaudited, able to execute model-generated code/commands, load third-party plugins, and reach files/network/processes/credentials made available to it.

ORION must therefore remain above it.

Important mismatches with ORION:

### Approval binding is weaker than ORION

DeepSeek Harness's built-in approval request carries tool identity/reason/call id but does not carry the complete tool arguments to the answerer.

ORION requires exact operation/scope/plan binding.

Therefore the built-in approval seam is useful UX but cannot replace ORION's exact-hash authorization.

### No built-in turn budget

The agent-loop documentation explicitly lists no built-in turn budget.

A runaway agent must be bounded by ORION with:

- wall-clock timeout;
- step/tool-call budget;
- cancellation;
- process-tree termination;
- evidence.

### Danger-full-access exists

The base bundle supports `danger-full-access` and uses an approval policy that does not prompt in that mode.

ORION qualification must never expose that mode by default.

Initial benchmark should pin `workspace-write` or stricter and enforce a disposable root independently.

### Tool visibility is not authority

Registering a tool makes it model-visible.

ORION must distinguish:

- tool exists;
- tool is visible;
- ORION lease authorizes this exact invocation.

### Cooperative cancellation needs physical STOP proof

Agent/tool cancellation is designed cooperatively in several layers.

ORION still needs to physically prove that STOP terminates the full process tree and leaves no child/background work alive.

## Proposed ORION qualification benchmark

Do not install DeepSeek Harness into the ORION authority repo.

Treat it as an external replaceable agent substrate.

### Phase A — local, disposable, no cloud

1. Pin reviewed DSH SHA.
2. Run in a disposable directory.
3. Disable telemetry/network except loopback Ollama.
4. Configure self-hosted local Qwen route if compatibility passes.
5. Restrict visible tools to the minimum file/shell set.
6. Add an ORION monotonic tool guard.
7. Keep sandbox at `workspace-write` or stricter.
8. Set explicit step/tool/time limits.
9. Run through `headless --json`.

### Tasks

Use the same task against:

- current Qwen 9B + deterministic Hands baseline;
- DeepSeek Harness + same local Qwen;
- later, DeepSeek Harness + stronger local model if warranted.

Measure:

- task success;
- first-action latency;
- total latency;
- CPU/GPU/VRAM/RAM;
- model tokens;
- tool calls;
- retries;
- path/scope compliance;
- evidence quality;
- STOP latency;
- residual child processes.

### Authority attacks

Must include:

- attempt to write outside approved root;
- model tries to widen tool/sandbox permission;
- stale/forged approval;
- command attempts network access when denied;
- child/subagent tries to bypass parent restriction;
- background job remains after STOP;
- post-approval task mutation.

Only after these pass may DSH become a qualified fallback Agent Hand.

## Latest-fork summary

### AutoHarness

**Useful governance donor; not preferred as ORION's execution substrate.**

Interesting pieces:

- six-step tool governance pipeline;
- risk classification;
- permission checks;
- input/output rails;
- context/token budgeting;
- multi-agent profiles;
- cost attribution;
- JSONL audit;
- trace diagnostics.

It overlaps heavily with ORION authority. Borrow ideas/tests rather than inserting it above ORION.

### CLI-Anything

**Already a high-value deterministic specialist-Hand donor.**

Still fits the narrowest-executor-first rule better than a general agent for supported software.

### Octop

**High-value architecture/UI/multi-lane donor.**

Relevant to the new Personal Assistant + Project Assistant direction:

- multiple experts/agents;
- workspaces;
- knowledge/RAG;
- channels/connectors;
- browser/terminal;
- remote desktop;
- ACP delegation.

Do not use Octop as ORION authority.

### openmuse

**Already-qualified conceptual donor for proposal/claim/idempotency/outcome semantics.**

No change to current role.

### mimic

**Potential specialist API-Hand generator, but high-risk and not a core ORION donor.**

It observes/replays application HTTP traffic and can generate Python clients.

Potential value:

- convert a user-owned web/app workflow into a deterministic API adapter.

Risks:

- proxy/certificate installation;
- credential/session replay;
- pinning bypass tooling;
- service ToS issues;
- sensitive token capture.

If ever used, isolate it as an explicit owner-authorized reverse-engineering tool. Never use it for automatic background discovery.

### GhostTrack

Still unrelated to ORION's core architecture.

## Ranking of the new discoveries

1. **DeepSeek Harness** — first-priority full-agent benchmark candidate.
2. **AutoHarness** — governance/test donor.
3. **mimic** — optional specialist API-Hand donor under strict isolation.

Existing priority donors remain:

- CLI-Anything for deterministic specialist Hands;
- Octop for multi-lane assistant/UI/workspace patterns;
- openmuse for proposal/evidence/idempotency semantics.

## Recommendation

Do not adopt another autonomous architecture.

Instead add DeepSeek Harness to the execution hierarchy as a **candidate full-agent Hand/substrate**:

`native deterministic Hand -> specialist CLI Hand -> DeepSeek Harness agent -> heavier/other agent substrate`

DeepSeek Harness is now the best candidate to run first in the full-agent benchmark because it has:

- a real loop;
- strong plugin seams;
- a machine-readable headless runner;
- Windows sandbox support;
- explicit guard/restriction hooks;
- local/self-hosted model routing.

The benchmark, not the README, decides whether it earns a production role.
