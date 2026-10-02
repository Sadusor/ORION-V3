# Gate 1 — OpenJarvis Foundation

## Purpose

Falsify the claim that OpenJarvis can serve as generic substrate while ORION remains sole authority.

## Operation

`filesystem.search` only.

## Current status

**PARTIAL PHYSICAL PASS.**

The real pinned OpenJarvis authority/executor integration passed on Windows at:

- ORION-V3: `98edcd5e018ad60cae18c8654bff289e69ab0e70`
- OpenJarvis: `309a4f1044ccfb2032264832a31fef2f1d314586`
- ORION Remote attempt: `397`
- result: `PASS`

Observed:
- 16/16 authority tests PASS;
- real OpenJarvis Rust extension PASS;
- no ORION lease -> denied before dispatcher;
- valid ORION lease + Jarvis capability -> dispatcher reached;
- model/tool trust-binding override -> denied.

Evidence:
`docs/journal/2026-10-03-gate1-openjarvis-physical-authority-pass.md`

## Required physical path

owner/Qwen intent -> OpenJarvis registered ORION proxy -> ORION Gateway -> valid lease -> bounded deterministic filesystem Hand -> ORION evidence -> verifier

## PASS requirements

- no lease is denied before Hand invocation — **PHYSICAL PASS for real ToolExecutor path**;
- forged/expired/revoked/wrong-scope leases are denied — **AUTOMATED PASS**;
- trusted roots cannot come from model/tool args — **PHYSICAL PASS for real ToolExecutor path**;
- search cannot widen itself into reveal — **AUTOMATED PASS**;
- Jarvis policy is default-deny — IMPLEMENTED / source-audited;
- Jarvis native agent cannot bypass the ORION proxy boundary — **PENDING PHYSICAL FALSIFIER**;
- direct Jarvis capability grants cannot mint ORION authority — **PENDING PHYSICAL FALSIFIER**;
- ORION evidence, not model prose, determines outcome — IMPLEMENTED / further physical path pending;
- donor event history is non-canonical — DOCUMENTED / dedicated falsifier pending;
- timeout is not reported as Stop — **PENDING PHYSICAL FALSIFIER**;
- old ORION repository and Remote remain untouched architecturally — PASS for this gate.

## Lease transport correction

Real OpenJarvis execution showed that a Python `ContextVar` does not cross the donor executor's worker-thread boundary.

Gate 1 therefore uses an **ephemeral lease-bound ORION proxy instance**:
- token captured privately by ORION;
- token absent from model-facing schema;
- token cannot be injected through tool arguments;
- unbound proxy remains denied;
- Jarvis remains a second fail-closed gate.

## Physical Stop falsifier

Use a deliberately blocking test Hand or donor worker.

A timeout result while underlying work continues is FAIL.

PASS requires:
1. ORION requests Stop;
2. the owned worker/process is terminated or otherwise verifiably cancelled;
3. liveness verification proves the underlying operation is gone;
4. only then may canonical outcome become STOPPED.

## Upgrade falsifier

Deliberately widen/alter the Jarvis-side capability policy in the test harness.
ORION denial must still prevent Hand invocation.

## Adoption

OpenJarvis becomes the preferred V3 substrate only after the remaining Gate-1 falsifiers physically pass.
