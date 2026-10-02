# Gate 1 — OpenJarvis Foundation

## Purpose

Falsify the claim that OpenJarvis can serve as generic substrate while ORION remains sole authority.

## Operation

`filesystem.search` only.

## Required physical path

owner/Qwen intent -> OpenJarvis registered ORION proxy -> ORION Gateway -> valid lease -> bounded deterministic filesystem Hand -> ORION evidence -> verifier

## PASS requirements

- no lease is denied before Hand invocation;
- forged/expired/revoked/wrong-scope leases are denied;
- trusted roots cannot come from model/tool args;
- search cannot widen itself into reveal;
- Jarvis policy is default-deny;
- Jarvis native agent cannot bypass the ORION proxy boundary;
- direct Jarvis capability grants cannot mint ORION authority;
- ORION evidence, not model prose, determines outcome;
- donor event history is non-canonical;
- timeout is not reported as Stop;
- old ORION repository and Remote remain untouched.

## Physical Stop falsifier

Use a deliberately blocking test Hand or donor worker.
A timeout result while underlying work continues is FAIL.
PASS requires verified donor cancellation or a killable worker boundary.

## Upgrade falsifier

Deliberately weaken/alter the Jarvis-side capability policy in the test harness.
ORION denial must still prevent Hand invocation.

## Adoption

OpenJarvis becomes the preferred V3 substrate only after every Gate-1 requirement physically passes.