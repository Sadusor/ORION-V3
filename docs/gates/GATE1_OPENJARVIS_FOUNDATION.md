# Gate 1 — OpenJarvis Foundation

## Status

**COMPLETE — PHYSICAL PASS**

Date: 2026-10-03

## Purpose

Falsify the claim that OpenJarvis can serve as generic substrate while ORION remains sole authority.

## Operation

`filesystem.search` only.

## Exact completion evidence

- ORION-V3: `dc13d5caddf2489879b2d300addaa5419b3d5975`
- OpenJarvis: `309a4f1044ccfb2032264832a31fef2f1d314586`
- ORION Remote: `df4ef699706ede0ce6d9de34eaeb74b84213a116`
- physical attempt: `399`
- result: **PASS**

Evidence:
`docs/journal/2026-10-03-gate1-complete.md`

## PASS requirements

- no lease denied before Hand invocation — **PASS**
- forged/expired/revoked/wrong-scope leases denied — **PASS**
- trusted roots cannot come from model/tool args — **PASS**
- search cannot widen itself into reveal — **PASS**
- Jarvis policy is default-deny in governed path — **PASS**
- native Jarvis agent cannot bypass ORION — **PASS**
- permissive/direct Jarvis capability posture cannot mint ORION authority — **PASS**
- timeout is not reported as Stop — **PASS**
- physical Stop verifies underlying work is gone — **PASS**
- ORION remains the authority above donor execution — **PASS**

## Physical Stop proof

The final Stop falsifier deliberately ran observable blocking work in an ORION-owned Windows worker process.

PASS required all of:

1. actual worker PID identified independently from launcher PID;
2. Windows process-tree termination requested for that PID;
3. Windows no longer reported the worker PID;
4. heartbeat ceased changing after termination;
5. only then was `PHYSICAL_STOP=PASS` emitted.

Observed:

```text
WORKER_PID_OS_ABSENT=PASS
UNDERLYING_WORK_GONE=PASS
PHYSICAL_STOP=PASS
```

## Donor timeout proof

OpenJarvis ToolExecutor timeout was physically shown to return while the timed-out Python function continued running.

Observed:

```text
DONOR_TIMEOUT_RETURNED_WHILE_WORK_CONTINUED=PASS
TIMEOUT_IS_NOT_STOP=PASS
```

Therefore donor timeout is never canonical ORION Stop evidence.

## Native bypass proof

A real OpenJarvis `NativeReActAgent` was given the ORION proxy with a deliberately permissive Jarvis capability policy but no ORION lease.

Observed:

```text
NATIVE_AGENT_BYPASS=DENIED
JARVIS_POLICY_WIDENING=NO_ORION_AUTHORITY
```

The dispatcher was not reached.

## Adoption decision

OpenJarvis is now the **preferred replaceable generic substrate** for ORION V3.

It is not the authority layer.

Canonical hierarchy:

```text
OWNER
  -> ORION AUTHORITY
      -> OpenJarvis substrate
          -> Hands
```

OpenJarvis security is retained as defense in depth and may narrow execution, but cannot widen ORION authority.

## Next gate

V3.1 — real deterministic filesystem Hands and normalized evidence, followed by desktop/UI substrate evaluation.
