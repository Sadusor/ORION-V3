# ORION V3 Roadmap

All milestones are gated by physical evidence.

The authoritative system direction is in `docs/ORION_SYSTEM_MODEL.md`.

## V3.0 — Foundation Gate 1 — COMPLETE

Proved OpenJarvis can be used as a replaceable substrate without becoming an
authority peer.

## V3.1 — Selective donor adoption — IN PROGRESS

Keep donor-first execution rules, but do not confuse low-level donor tools with
the higher-level ORION semantic Capability Registry.

Completed/proven:
- OpenJarvis ToolRegistry/ToolExecutor under ORION authority;
- custom missing `filesystem.search` extension only where donor lacked it;
- OpenJarvis WorkflowEngine mechanics under ORION authority;
- Qwen3.5-9B one-shot routing candidate;
- OpenHands FileEditor/Windows Terminal Hands-only qualification.

Current correction:
- stop wrapping primitive coding commands one-by-one as the main direction;
- harvest proven implementations into semantic capabilities;
- keep heavy coding agents as optional semantic Coding Hands.

## V3.2 — Capability Registry + lightweight governor

Priority:
1. inventory capabilities already physically present in legacy ORION Remote,
   V3, OpenJarvis and native Windows/PowerShell;
2. define one semantic Capability contract;
3. batch-register/harvest the first useful capability pack;
4. benchmark Qwen3.5-9B on natural language -> literal semantic Intent/entities;
5. canonicalize Intent/entities deterministically;
6. resolve canonical Intent -> capability deterministically;
7. make ORION deterministic policy choose implementation/risk/approval.

Qwen must not write arbitrary shell as the normal path.

## V3.3 — Canonical Memory + local event exchange

Memory is now an early foundation, not a late enhancement.

Primary donor: KnowledgeOS.

Build/prove:
- project facts;
- decisions;
- current state;
- failure lessons;
- capability knowledge;
- evidence references;
- progressive L0/L1/L2 retrieval;
- project/task hard scoping;
- append-only PROPOSAL/REVIEW/DECISION/ACTION/EVIDENCE/RESULT event log.

Goal:
a new/replacement model can reconstruct enough current project state to resume
correctly after months/years without reading the full raw history.

GitHub remains source control, not the long-term AI<->PC mailbox.

## V3.4 — Coding Factory workflow

Automate the currently manual reasoning loop around already-proven Coding Hands.

Physically proven foundation:
- V3-RUN-018: immutable content-addressed Artifact Store;
- exact-SHA/scope-bound WorkPackage;
- package-bound PROPOSAL -> REVIEW -> DECISION;
- accepted candidate still has zero execution authority;
- V3-RUN-019: durable Attempt ownership, fenced lease generations, checkpoint
  enforcement, stale-worker rejection, restart recovery and ORION-owned Stop.

Immediate gated sequence:
1. **COMPLETE — V3-RUN-020:** isolated exact-SHA Git worktree execution envelope;
2. **COMPLETE — V3-RUN-020:** harmless approved PATCH/FILE execution under the
   current Attempt lease;
3. **COMPLETE — V3-RUN-020:** exact changed paths, diff/tree evidence and
   deterministic verification;
4. **COMPLETE — V3-RUN-020:** cleanup on PASS/FAIL/Stop with no push/merge/commit;
5. **CURRENT — OpenHands diagnostic isolation after RUN-021..027:** the mature
   Coding Hand benchmark exposed a tool-call behavior mismatch in the full
   OpenHands Agent/Conversation path. Native Ollama, direct LiteLLM, and direct
   OpenHands LLM wrapper tool calls are physically healthy; isolate the exact
   Agent-prepared system prompt/messages/history difference before scoring or
   swapping more models.
6. after the Agent-path issue is explained, rerun the same bounded semantic
   Coding Hand benchmark and only then compare additional mature candidates;
7. connect real cloud coder/reviewer providers only after candidate mechanics
   are physically qualified.

Target:
- cloud architect AI;
- cloud reviewer/critic;
- optional additional review only when risk/disagreement justifies it;
- Qwen lightweight coordinator;
- existing/qualified Coding Hands;
- local tests/diff/evidence;
- ORION verifier;
- loop until PASS or human help is needed.

Cloud models remain replaceable and do not receive PC authority.

Benchmark semantic Coding Hands where useful:
- Claude Code;
- OpenHands;
- OpenJarvis native OpenHands/orchestration only if it adds measurable value.

Do not rebuild mature internal coding command sequencing if a candidate passes.

## V3.5 — Browser capability/workflow layer

Inventory/reuse OpenJarvis browser tools and compare serious donors:
Aegis, PinchTab, CUA browser mode and specialist extraction donors.

Known browser operations should remain deterministic capabilities.
Novel interactive web workflows may escalate.

## V3.6 — Whole-PC Computer Hand

Escalation path for GUI/desktop tasks not expressible as known capabilities.

Candidates:
- CUA Driver;
- UI-TARS / UI-TARS Desktop;
- Qwen vision;
- OpenBot patterns;
- OpenMuse isolated-computer patterns.

Must prove:
- containment;
- bounded scope;
- Stop;
- evidence;
- no authority widening.

## V3.7 — Capability promotion / learning policy

Do not auto-trust agent traces.

Use evidence + repeated success + deterministic extraction + test replay +
scope/contract review + explicit promotion.

Learning means reusable verified memory/capability, not raw self-training.

## V3.8 — Android / device

Primary donor: Artemis.
Transport/client donors: KIRA and Orion-Copilot patterns.

## V3.9 — Connectors / commodity workflows

Primary donor: n8n where useful.

## V3.10 — ORION-owned Jarvis-style interface

Use selected OpenJarvis/OpenMuse frontend/runtime pieces where helpful.

Product direction is ORION-owned with jarvis.institute as UX/product inspiration:
- central visual state;
- Ready/Thinking/Running/Waiting/Approval;
- chat;
- activity;
- conclusions;
- timeline;
- later voice;
- PC/phone parity.

The interface consumes ORION state; it never becomes canonical truth.

## V3.11 — Voice / channels

Candidates:
OpenJarvis channel plumbing, whisper.cpp, EchoFetch, openWakeWord, Kokoro.

## V3.12 — Remote parity / retirement decision

Legacy ORION Remote remains the proven transport/fallback while V3 matures.

Only after equivalent PC + phone execution, Stop, evidence and recovery are
physically proven may the old Remote be considered for retirement.
