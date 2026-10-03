# DeepSeek operator-architecture review — ORION response

Date: 2026-10-04

## Review received

Independent reviewer: DeepSeek.

The review strongly agrees with ORION's core invariant:

- the model proposes;
- ORION owns authority;
- canonical Task/Attempt state, policy, approvals, leases, WorkPackages,
  evidence, verification, Stop and Memory promotion remain external to the model.

It also agrees that:
- Hands can be exposed to the model as tool-shaped interfaces;
- OpenHands should be treated as a donor rather than an authority peer;
- OpenJarvis provides useful registry/executor/workflow patterns;
- cloud AIs can be exposed as probabilistic capabilities;
- phone approval should bind to an exact immutable WorkPackage/hash;
- an ORION Operator Benchmark is more relevant than benchmarking one donor as
  the product.

## Important correction: Qwen role is two-lane, not one-lane

DeepSeek recommends that Qwen never select capability IDs and only emit
Intent/entities.

ORION will keep that rule for the **fast deterministic lane**, but not for all
operator work.

### Lane A — deterministic routine lane

For known, unambiguous, common operations:

`user -> Qwen Intent/entities -> canonicalizer -> deterministic resolver ->
policy -> capability -> Hand -> evidence/verifier`

Qwen does not select implementation IDs here.

Examples:
- open Chrome;
- status;
- approve the single pending WorkPackage;
- start Ollama;
- run a known project test workflow.

### Lane B — scoped agentic operator lane

For novel or genuinely multi-step work:

`user -> Qwen operator -> scoped allowed tool catalog -> proposed tool call ->
ORION validation/policy -> Hand -> observation -> Qwen next proposal`

Qwen may choose among the capabilities ORION has exposed for that task, but:
- it cannot widen the tool set;
- it cannot widen scope;
- it cannot authorize itself;
- every tool call is validated before effect;
- every effect is evidenced and can be verified;
- approval-class actions remain bound to exact immutable state.

This preserves the desired natural phone/PC operator experience without turning
Qwen into the security boundary.

## Control-loop distinction

There are two loops:

1. **proposal/planning loop** — may be model-driven;
2. **authority/execution loop** — always ORION-driven.

This is the important boundary, not the binary phrase "Qwen is/is not the
control loop."

## Tool vs Hand

Model-visible:
- typed tool/capability name;
- description;
- typed parameters;
- result schema.

ORION-internal:
- Hand implementation;
- permission envelope;
- scope;
- approval class;
- timeout;
- lease;
- evidence contract;
- verifier;
- Stop behavior.

A model tool call is a proposal.
A Hand is the bounded executor ORION may dispatch after validation.

## Donor roles

### OpenHands

Borrow/test:
- FileEditorTool;
- TerminalTool;
- Browser tools where useful;
- Action/Observation/Executor contracts;
- selected Conversation/Agent machinery only if physically useful.

Reject:
- stock 15k system prompt for Qwen;
- donor authority/security policy as ORION authority;
- assumption that the donor Agent must own orchestration.

RUN-031 is the physical decision gate for whether compact-prompt OpenHands Agent
machinery remains worth keeping.

### OpenJarvis

Borrow selectively:
- registry/discovery patterns;
- OpenAI-compatible tool-schema generation;
- central executor pattern;
- trace/event patterns;
- workflow patterns;
- existing useful tools.

Do not copy donor schemas blindly.

Pinned-source note:
the Python ToolSpec documentation and the Rust ToolSpec/executor surface are not
identical. The Python docs expose confirmation/cost/latency metadata, while the
Rust executor also enforces required capabilities. ORION should define one
canonical semantic capability contract that imports the useful fields without
duplicating donor implementation details.

## Cloud AIs

Treat cloud providers as probabilistic capabilities, for example:
- brainstorm;
- architecture review;
- code generation;
- code review;
- summarize.

Their outputs are proposals/evidence, never canonical execution truth.

## Phone interaction

The phone is a conversation endpoint to the same operator.

Example:
`idea -> Qwen -> brainstorm capability -> cloud AIs -> proposals -> ORION Event
Exchange -> Qwen summary -> phone`

Later:
`build -> Coding Hand -> WorkPackage -> reviewer -> WAITING_FOR_APPROVAL ->
phone -> "approve" -> Intent -> exact pending WorkPackage hash -> approval grant
-> ORION Hand -> verifier -> result`

Natural language never becomes generic permission.

## Benchmark target

The real target is **ORION Operator Benchmark v1**, not "OpenHands benchmark."

Model candidates initially:
- Qwen3.5-9B;
- Qwen3.6-35B-A3B.

Tool families:
- OpenHands donor tools;
- OpenJarvis donor tools;
- ORION-native Hands;
- cloud-AI capabilities.

Benchmark dimensions:
- correct routine intent;
- tool selection in scoped agentic lane;
- correct arguments;
- minimal calls;
- multi-step chaining;
- approval discipline;
- scope compliance;
- recovery;
- correct stopping;
- latency/resource use;
- zero authority bypass.

Any executed authority bypass, approval bypass, or scope violation is an
automatic failure.

## Do not repeat already-proven gates

DeepSeek's proposed next gates include work ORION already physically proved:
- semantic governor/canonicalizer/resolver: RUN-014;
- WorkPackage/approval-bound candidate architecture: RUN-018 + later envelope;
- durable Attempt/lease/Stop: RUN-019;
- exact-SHA bounded executor/evidence/verifier: RUN-020.

Do not restart those gates.

## Immediate physical sequence

1. **RUN-031:** compact ORION prompt through the real OpenHands Agent loop.
2. If PASS, test FileEditor + Terminal under the same compact prompt on the
   original bounded coding fixture.
3. Build the unified semantic Capability contract by harvesting selected
   OpenHands/OpenJarvis/ORION capabilities.
4. Build a small mixed-tool Operator Benchmark smoke set.
5. Compare Qwen 9B vs Qwen 35B on the same smoke set before scaling to the full
   benchmark.

If RUN-031 fails, skip OpenHands Agent orchestration and integrate its useful
tools directly behind the ORION operator loop.
