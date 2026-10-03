# ORION V3 — Contributor / AI Instructions

This file is authoritative for work in `Sadusor/ORION-V3`.

## Identity

ORION V3 is a clean experimental rebuild using mature donor infrastructure where it survives ORION authority contracts.
It is NOT the old ORION repository. Do not modify or retire the proven old Remote while V3 is experimental.

## Authority hierarchy

OWNER > ORION AUTHORITY > SUBSTRATE / DONORS > HANDS

ORION always owns:
- canonical Task/Event truth;
- PermissionGrants and Action Leases;
- approvals;
- privacy and budgets;
- operation authorization;
- evidence normalization and verification;
- Stop/recovery truth;
- canonical Memory promotion;
- continuity/restart semantics.

No donor is a co-authority.

## OpenJarvis rule

Preferred substrate candidate: `Sadusor/OpenJarvis@309a4f1044ccfb2032264832a31fef2f1d314586`.

On ORION-governed paths:
- OpenJarvis capability policy is fail-closed / default-deny;
- Jarvis security may only narrow authority, never create ORION authority;
- autonomous Jarvis agents do not receive unrestricted side-effect tools;
- EventBus is telemetry/transport, never canonical Task/Event truth;
- Jarvis timeout is NOT ORION Stop.

## Mandatory donor gate

Before substantial custom implementation:
1. classify the ORION layer;
2. inspect internal/proven ORION mechanics;
3. inspect serious donors;
4. **inventory the pinned OpenJarvis registry and built-in tools before writing any tool/Hand code;**
5. prefer configuring, adapting or wrapping an existing donor tool over reimplementing its capability;
6. compare security, Stop, evidence, Windows behavior, license and replaceability;
7. run the smallest falsification spike;
8. record the result;
9. custom-build only when donors genuinely lack the capability or fail a real ORION contract.

A missing capability should normally be added as an OpenJarvis-native registered tool, not as a second ORION execution framework.

## Old ORION protection

Fallback reference only:
- repo: `Sadusor/Orion`
- branch: `checkpoint/2026-10-01-orion-remote-project-link`
- SHA: `327d32f714129ca633517a8f4158cd84820c1504`

Do not push V3 experiments into that repository.

## Cost / supply chain

- Prefer local tests.
- No surprise paid APIs or hosted compute.
- No automatic GitHub Actions triggers without owner approval.
- Pin donor revisions used in physical gates.
- Do not execute downloaded donor installers/scripts merely because upstream says to.
- Never commit secrets, private logs or personal data.

## Public repository rule

ORION-V3 is currently public. Fixtures must be synthetic.

## Evidence labels

DOCUMENTED / GITHUB-CODED-UNVERIFIED / AUTOMATED PASS / PHYSICAL PASS / PARTIAL / FAIL / BLOCKED / NOT TESTED

## Workflow-first rule

ORION is workflow-first, not autonomous-agent-first.

Normal execution:
- owner / strong external AI chat supplies reasoning or intent;
- ORION chooses or constructs a bounded workflow;
- ORION owns authority, leases, trusted bindings, Stop and evidence;
- donor Hands/tools execute the bounded steps;
- results/evidence return to the owner or reasoning source.

OpenJarvis autonomous agent loops are donor candidates only. Do not make
`orchestrator`, `native_react`, `native_openhands`, managed agents or
other self-looping donor agents the default ORION control plane.

A local model may be used as a low-cost helper for a narrowly defined job
such as one-shot classification/routing. It must not gain authority merely
because OpenJarvis calls it an agent.

Prefer in order:
1. deterministic workflow with no inference;
2. one-shot bounded local routing/planning when needed;
3. strong external AI chat reasoning plus ORION Hands;
4. autonomous/multi-turn agent loops only as explicit, separately qualified
   capabilities when a workflow cannot reasonably do the job.

## Product interface direction

The final ORION interface is ORION-owned.

- Stanford OpenJarvis is an infrastructure/tool/runtime donor.
- `jarvis.institute` is a product/UX reference, not the OpenJarvis source tree.
- Do not turn the stock OpenJarvis desktop into the final product by accident.
- Reuse useful OpenJarvis frontend/runtime components selectively.
- Continue the ORION-specific interface after donor capability qualification,
  using publicly observable Jarvis Institute UX/workflow ideas where useful.

## Architecture freeze — 2026-10-03

Read `docs/ORION_SYSTEM_MODEL.md` before changing architecture.

Do not conflate:
- ORION Core;
- the Coding Factory workflow;
- the lightweight personal assistant;
- the Whole-PC Computer Hand;
- the ORION-owned Jarvis-style interface.

### Qwen governor rule

Qwen3.5-9B is a semantic governor candidate, not an authority layer.

Qwen may infer intent, entities, ambiguity and small compositions.
Qwen must not choose risk policy, mint permissions, widen scope, declare PASS,
promote Memory or write arbitrary shell as the normal control path.

Rule: **Qwen proposes; ORION disposes.**

### Semantic Capability Registry rule

ORION may maintain a semantic/policy Capability Registry without violating the
ban on a parallel low-level Hand/tool registry.

The distinction is mandatory:
- OpenJarvis/donor ToolRegistry = concrete low-level implementation/tool registry;
- ORION Capability Registry = stable semantic intent, typed params, policy,
  trusted scope, implementation binding, Stop/evidence/postcondition contract.

Do not register a capability and assume it is safe. Implementations must
validate before effects and ORION must verify evidence/postconditions after.

### Guard rule

Do not solve routine guard friction by deleting the guard.

Preferred normal path:
`typed intent -> registered capability -> deterministic policy -> vetted implementation`.

Direct, unambiguous user requests should count as authorization for routine
bounded Class-0/Class-1 actions where policy says so. Avoid redundant prompts.

### Coding Factory rule

The Coding Factory is a workflow on ORION Core.

Existing Coding Hands are already proven useful. Do not rebuild coding command
sequencing one primitive at a time merely because a donor exposes file/shell tools.

A mature coding agent may be treated as one semantic Coding Hand when useful,
inside a bounded workspace/envelope with ORION-owned Stop and verification.

### Memory rule

Continuity is a primary system requirement.

Canonical project state, decisions, failures/lessons, capabilities and evidence
must be reconstructable without relying on chat/model memory.

PASS/FAIL records are evidence, not auto-training data. Promotion to canonical
Memory requires provenance, contradiction handling and an explicit gate.

### Current priority

Do not run staged `V3-RUN-009` as the next step.

Current work order:
1. inventory proven existing capabilities;
2. define semantic Capability contract;
3. harvest/register a first batch;
4. benchmark Qwen intent routing;
5. implement canonical Memory + local append-only exchange;
6. automate Coding Factory;
7. Whole-PC escalation later.
