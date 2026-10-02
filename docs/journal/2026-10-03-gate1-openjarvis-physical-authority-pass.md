# Gate 1 OpenJarvis authority/executor integration — physical result

Date: 2026-10-03  
Status: **PHYSICAL PASS — authority/executor integration slice**

## Exact tested identities

ORION-V3:
`98edcd5e018ad60cae18c8654bff289e69ab0e70`

OpenJarvis donor:
`Sadusor/OpenJarvis@309a4f1044ccfb2032264832a31fef2f1d314586`

ORION Remote transport task:
`Sadusor/Orion@07e65bb00be29746b201bdeffead68ddcf9a4867`

Remote physical attempt:
`397`

Remote result:
`PASS`

## Physical evidence

The Windows PC executed the V3 bootstrap through the proven ORION Remote path.

Observed PASS markers:

```text
V3_EXACT_SHA> PASS
V3_AUTHORITY_TESTS> PASS
OPENJARVIS_PIN> PASS
OPENJARVIS_ENV> PASS
GATE1_OPENJARVIS_SMOKE=PASS
NO_LEASE=DENIED
AUTHORIZED_DISPATCH=PASS
TRUST_BINDING_OVERRIDE=DENIED
OPENJARVIS_GATE1_SMOKE> PASS
ORION_REMOTE_TO_V3_GATE1> PASS
STATUS> PASS
```

Authority unit suite:
`16 passed`

The real OpenJarvis Rust extension built and loaded on Windows.

## Important design correction discovered by physical testing

The first real OpenJarvis execution exposed that `ContextVar` lease binding does not survive the donor executor's worker-thread boundary.

The design was corrected rather than weakened:

- ORION now creates an **ephemeral lease-bound proxy tool instance** for an authorized dispatch.
- the lease token remains private to the proxy instance;
- the lease is not present in the model-facing ToolSpec;
- the lease is not accepted from tool/model arguments;
- an unbound/native proxy call remains discoverable but is denied by the ORION Gateway;
- Jarvis capability policy remains a second fail-closed gate, not the source of ORION authority.

This physical result therefore falsified the original context-propagation assumption and produced a stronger integration boundary.

## What this PASS proves

For the tested `filesystem.search` proxy:

1. real pinned OpenJarvis can host the ORION proxy on the owner's Windows machine;
2. the OpenJarvis Rust security dependency is operational;
3. Jarvis execution without an ORION Action Lease does not reach the dispatcher;
4. a valid ORION lease plus Jarvis capability allow reaches the dispatcher;
5. model/tool arguments cannot replace ORION-owned trust bindings;
6. ORION authority remains outside the donor executor.

## What this PASS does not prove

Gate 1 is **not complete** yet.

Still required:

- native Jarvis agent/direct-tool bypass falsifier beyond the current unbound ToolExecutor probe;
- explicit Jarvis-side capability-widening falsifier while ORION denies;
- blocking Hand physical Stop/cancellation proof;
- proof that timeout alone is never promoted to STOPPED;
- donor EventBus/session state remains non-canonical;
- upgrade/replacement simulation preserves ORION authority.

## Next bounded gate

Run two physical falsifiers:

1. **native-agent/direct-bypass** — attempt execution through a Jarvis-native path without an ORION lease and prove dispatcher count remains zero;
2. **physical Stop** — deliberately start blocking work, terminate the ORION-owned killable worker, and verify the underlying work is actually gone before emitting STOPPED.

Only after those pass should Gate 1 be considered complete or OpenJarvis be promoted from candidate to adopted V3 substrate.
