# ORION V3 — AI Operator Brief

## CURRENT OWNER PRIORITY — Qwen + ORION Hands Autonomous Work Loop V1

The active project is the existing Autonomous Work Loop V1: Vault STATE -> Qwen typed proposal -> ORION policy/authorization -> ORION Work Hand -> independently verified evidence -> Vault STATE/JOURNAL. First test the existing coordinator and connect Qwen with offline contracts. Real execution remains disabled until Windows isolation and STOP/commit qualification pass. The main physical milestone is FAIL -> restart -> fresh Qwen -> repair -> PASS. Cloud specialists, Skills and Work UI come later.

TheHands is a separate product and may inform remote UX only. It is not the ORION Work Hand, a test runner, a code or evidence dependency, or a runtime adapter. Older instructions below that direct use of its GitCheck workflow are historical, not active. Decision 0019 controls the current work. Do not add parallel authority, Vault, STOP or memory systems.

## 1. Prime directive

ORION V3 is a modular deterministic authority/work system around replaceable AI reasoning and execution components.

```
OWNER
  ↓
ORION — policy / authority / approvals / STOP / canonical state
  ↓
Models — propose, reason, plan, review
  ↓
Hands / tools — bounded execution
  ↓
Independent verification
  ↓
ORION records verified truth
```

Models are not authority. Hands are not authority. Memory is not authority. UI is not authority. A component reporting PASS does not make something true.

Optimize for owner authority, deterministic behavior, evidence, replaceable modules, bounded execution, low CPU/GPU/idle consumption, recoverability, testability, and simple solutions. Avoid unnecessary agent loops, architecture creep, duplicate systems, and rewriting proven modules.

## 2. TheHands is separate — do not confuse it with ORION

**TheHands is NOT ORION.** It is an independent Android → Windows remote-control application with its own GitHub repository. We built and physically proved it so the owner can work remotely.

TheHands provides the established remote development/test path, including GitCheck, explicit Approve & Start, Manual PowerShell, execution output, STOP controls, and GitHub-published evidence.

During ORION development, treat TheHands as a **development transport/test executor**, not ORION's authority layer. Do not merge its architecture into ORION. Do not modify TheHands product code unless the owner explicitly authorizes it. When the established workflow permits staging ORION tests through TheHands, touch only the designated test-command interface.

If you need to understand remote operation, inspect the separate TheHands repository and its documentation rather than guessing.

## 3. Start every fresh session by recovering project truth

Before proposing or changing anything:

1. Inspect the ORION V3 repository.
2. Find/read the current STATUS, LATEST/checkpoint, roadmap, relevant invariants and decisions.
3. Read documentation for the active module.
4. Inspect that module's implementation and tests.
5. Inspect recent verified evidence/results when relevant.
6. Check whether the module is frozen.
7. Only then choose the smallest bounded next action.

Do not make the owner reconstruct project history if the repository contains it.

When sources disagree, use this precedence:

```
PHYSICAL VERIFIED EVIDENCE
    >
CURRENT CODE
    >
CURRENT CANONICAL PROJECT STATE
    >
OLDER DOCUMENTATION
    >
MODEL ASSUMPTION
```

Flag contradictions. Do not silently guess.

## 4. How development normally works

The owner often works remotely through TheHands:

```
AI inspects ORION + docs
    ↓
choose ONE bounded change/test
    ↓
implement in ORION V3
    ↓
stage regression through established TheHands GitCheck path
    ↓
owner: GitHub Check → Approve & Start
    ↓
Windows machine executes test
    ↓
TheHands publishes evidence
    ↓
AI retrieves ACTUAL evidence
    ↓
PASS → document/freeze/proceed
FAIL → inspect/fix/retest
```

Prefer GitCheck over asking the owner to type PowerShell manually. Manual PowerShell is a fallback or deliberate physical-test mechanism.

When the owner says **Pass / Passed / Fail / Failed**, retrieve actual evidence where available. Verify source commit, result, pass/fail/skipped counts, relevant output, and whether the intended code was actually tested. Do not guess.

## 5. Repository boundaries and frozen modules

Actual ORION development belongs in ORION V3. TheHands is separate. Do not modify unrelated repositories.

If a module is proven and frozen, treat it as an invariant unless a regression proves it broken, a genuine new requirement requires reopening it, or the owner explicitly authorizes the change.

Use modules where separation provides real isolation/replacement value. Do not split trivial behavior into needless architecture.

## 6. Working style

Act like an engineering partner, not a tutorial generator.

Default loop:

**ACT → TEST → VERIFY → DOCUMENT → NEXT**

Keep active-development explanations concise. Explain architecture in simple physical terms when requested.

Do not repeatedly ask “Would you like me to continue?” when the approved next bounded action is already clear and safe. Handle small implementation details required by an approved task. Ask before changing architecture, frozen boundaries, destructive behavior, credentials, real-machine authority, or other major risk boundaries.

## 7. Testing discipline

Prefer small regression tests proving one meaningful architectural property. Before adding a test, ask:

> **What architectural claim does this test prove?**

Do not grow test counts for appearance.

High-value adversarial areas include authority, evidence, scope, STOP, replay, stale state, path boundaries, race conditions, crash/recovery, model/tool impersonation and canonical-state mutation.

Do not expand security testing forever. Once the important boundary is proven, **freeze the module and move forward**.

Never confuse Python/application checks with an OS security sandbox. Be precise about what evidence proves. Fail closed at authority boundaries.

## 8. Documentation discipline

Important architecture decisions, failures, lessons, donor decisions, verified test results and freeze points must survive outside chat.

Do not create giant duplicate documents for tiny changes. Update canonical status/checkpoint/roadmap/journal documents appropriately.

The repository should let another AI determine:

- what we are building and why;
- what is physically/cryptographically/regression proven;
- what failed;
- what is frozen;
- the active module;
- the next bounded milestone;
- what must not be touched;
- what evidence supports current status.

## 9. Models, donors and low-consumption design

Models are replaceable reasoning resources. Prefer a lightweight local model for fast/common work and cloud intelligence/review when useful. ORION must not depend on one vendor or require a permanently running heavyweight autonomous agent if deterministic routing + small local model + cloud intelligence works.

Before building a substantial subsystem from scratch, inspect ORION donor research and relevant donor code. Known donor/reference areas include OpenJarvis, OpenHands, OpenViking, TencentDB Agent Memory, agentmemory, Aider repo-map, Serena, CUA/computer-use projects, KIRA, and documented security/agent projects.

Borrow useful components/patterns; do not surrender ORION's authority to a donor framework.

## 10. Memory, UI and STOP

Memory provides context, not authority. It must remain provenance-backed, scoped, replaceable and rebuildable, and must never override policy, owner instructions or canonical state.

PC/phone UI surfaces backend truth; UI code does not own policy authority. TheHands UI and future ORION UI are separate systems.

STOP is first-class authority. Every real-execution design must answer: **What happens if STOP occurs at the worst possible moment?** If unclear, that execution path is not ready.

## 11. Before implementing any change

Internally answer:

- What exact milestone are we working on?
- Which module owns this behavior?
- Is it frozen?
- Is donor code relevant?
- What is the smallest implementation that proves the requirement?
- What test proves it?
- What existing functionality could break?
- Does this affect TheHands?
- Does this alter an authority boundary?
- What documentation needs updating after proof?

Investigate before coding if any answer is materially uncertain.

## 12. After PASS / FAIL

After PASS: verify actual evidence, record what was proven, update relevant documentation, decide whether the boundary/module should freeze, and identify the next roadmap milestone.

After FAIL: do not immediately redesign. Determine whether it is an implementation failure, regression, test bug, environment limitation, incorrect assumption, integration issue, or genuine security-boundary violation. Fix the correct layer while preserving proven components.

## 13. Session-start instruction for any AI

On receiving or discovering this brief:

1. Read the current ORION V3 canonical project documents.
2. Determine the latest **verified** checkpoint.
3. Identify the active milestone/module and freeze status.
4. Inspect relevant implementation/tests.
5. If remote testing is needed, inspect enough of the separate TheHands repository/documentation to understand the established GitCheck workflow.
6. Do not modify TheHands except through an explicitly authorized interface.
7. Briefly report:

```
CURRENT VERIFIED STATE
ACTIVE MILESTONE
FROZEN / DO-NOT-TOUCH AREAS
NEXT BOUNDED ACTION
WHY THAT ACTION IS NEXT
```

Then **continue the existing project instead of inventing a new roadmap**.

---

## Permanent rule

**This file describes HOW to work on ORION. Current canonical project documents and verified evidence determine WHERE ORION is.**

