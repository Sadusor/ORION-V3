# Gate 1 completion — OpenJarvis substrate under ORION authority

Date: 2026-10-03  
Status: **PHYSICAL PASS / GATE COMPLETE**

## Exact physical evidence

ORION-V3 tested SHA:
`dc13d5caddf2489879b2d300addaa5419b3d5975`

Pinned OpenJarvis donor:
`Sadusor/OpenJarvis@309a4f1044ccfb2032264832a31fef2f1d314586`

ORION Remote transport SHA:
`Sadusor/Orion@df4ef699706ede0ce6d9de34eaeb74b84213a116`

Remote attempt:
`399`

Result:
`PASS`

## Physically observed PASS evidence

```text
V3_AUTHORITY_TESTS> PASS
OPENJARVIS_PIN> PASS
OPENJARVIS_ENV> PASS

GATE1_OPENJARVIS_SMOKE=PASS
NO_LEASE=DENIED
AUTHORIZED_DISPATCH=PASS
TRUST_BINDING_OVERRIDE=DENIED

NATIVE_AGENT_BYPASS=DENIED
JARVIS_POLICY_WIDENING=NO_ORION_AUTHORITY

DONOR_TIMEOUT_RETURNED_WHILE_WORK_CONTINUED=PASS
TIMEOUT_IS_NOT_STOP=PASS

WORKER_PID_OS_ABSENT=PASS
UNDERLYING_WORK_GONE=PASS
PHYSICAL_STOP=PASS

GATE1_REMAINING_FALSIFIERS=PASS
STATUS> PASS
```

Authority suite:
`16 passed`

## What Gate 1 now proves

For the bounded `filesystem.search` slice:

1. ORION Action Leases are the authority source.
2. OpenJarvis may host/execute the ORION proxy but cannot mint ORION authority.
3. A native OpenJarvis ReAct agent cannot bypass the ORION Gateway.
4. Even a permissive Jarvis capability policy cannot widen ORION authority.
5. Model/tool parameters cannot inject ORION-owned trust bindings.
6. Jarvis timeout is explicitly not treated as Stop.
7. ORION can own a killable worker process and only declare STOPPED after:
   - termination is requested,
   - Windows no longer reports the worker PID,
   - observed work no longer progresses.
8. The real pinned OpenJarvis Rust security runtime works on the owner's Windows machine.
9. The donor remains replaceable because canonical authority and Stop truth live above it.

## Important corrections discovered by physical falsification

### Lease propagation

The initial `ContextVar` design failed because OpenJarvis executes tool bodies on a worker thread.

Correction:
- ORION creates an ephemeral lease-bound proxy instance;
- the lease is private to that proxy;
- the lease is absent from the model-facing schema;
- unbound/native calls fail closed.

### Stop

The initial process harness assumed launcher PID == worker PID.

Correction:
- the worker reports its own PID;
- ORION Stop targets the actual owned worker process tree;
- OS absence and work cessation are separately verified.

These failures improved the design and are retained as regression evidence.

## Gate decision

**OpenJarvis is accepted as the preferred generic substrate for ORION V3.**

This does **not** make OpenJarvis the control plane.

Hierarchy remains:

```text
OWNER
  -> ORION AUTHORITY
      -> OpenJarvis substrate
          -> bounded Hands
```

Jarvis security remains a useful second fail-closed gate, but never the source of PermissionGrants, Action Leases, canonical evidence, or Stop truth.

## Next stage

Proceed to V3.1:

- turn `filesystem.search` from synthetic dispatcher into a real deterministic Hand;
- add bounded list/reveal operations as separate permissions;
- preserve lease-per-operation semantics;
- normalize real filesystem evidence;
- then begin desktop/UI evaluation and bring useful OpenJarvis desktop infrastructure under the same ORION boundary.
