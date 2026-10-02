# ORION V3 Status

Updated: 2026-10-03

## Stage

**Gate 1 COMPLETE — V3.1 donor-first OpenJarvis tool adoption in progress.**

ORION-V3 is a separate repository from the proven legacy ORION implementation.

## Gate-1 claims

- OpenJarvis substrate: **ADOPTED AS REPLACEABLE SUBSTRATE**
- ORION remains sole authority: **PHYSICALLY PROVEN for Gate-1 scope**
- Authority Boundary V0: **PHYSICAL PASS**
- ORION authority unit contract: **AUTOMATED PASS (16/16)**
- real pinned OpenJarvis + Windows integration: **PHYSICAL PASS**
- native Jarvis bypass falsifier: **PHYSICAL PASS**
- Jarvis policy widening falsifier: **PHYSICAL PASS**
- timeout != Stop falsifier: **PHYSICAL PASS**
- ORION-owned killable worker Stop: **PHYSICAL PASS**

## Gate-1 evidence identity

ORION-V3 tested SHA:
`dc13d5caddf2489879b2d300addaa5419b3d5975`

OpenJarvis:
`Sadusor/OpenJarvis@309a4f1044ccfb2032264832a31fef2f1d314586`

Legacy ORION Remote transport task:
`df4ef699706ede0ce6d9de34eaeb74b84213a116`

Legacy Remote transport record:
`attempt 399`

That number is **not an ORION-V3 attempt count**. It is retained only to locate the external transport evidence.

## ORION-V3 run numbering

ORION-V3 has its own sequence beginning with:

`V3-RUN-001`

Legacy ORION Remote attempt counters are never counted as V3 development runs.

## V3.1 architecture correction

Active branch:
`agent/v3.1-openjarvis-tools`

A parallel `orion_v3.hands` design was drafted on an obsolete branch but rejected **before physical execution** because it duplicated the substrate we had just adopted.

The active architecture is:

```text
OWNER
  -> ORION authority / Action Lease / trusted bindings / evidence / Stop truth
      -> OpenJarvis ToolRegistry + ToolExecutor
          -> existing OpenJarvis tool
             OR smallest OpenJarvis-native extension for a demonstrated gap
```

There is no second ORION tool/Hand registry.

## V3.1 donor inventory

At pinned OpenJarvis revision `309a4f1044ccfb2032264832a31fef2f1d314586`:

- `file_read`: **REUSE DONOR BUILT-IN**
- `file_write`: **REUSE DONOR BUILT-IN**
- browser/web/shell/patch/memory tools: **INVENTORY/QUALIFY BEFORE CUSTOM CODE**
- exact-basename local `filesystem.search`: no dedicated built-in found, therefore one minimal custom **OpenJarvis-registered** extension is justified.

The extension:
- subclasses OpenJarvis `BaseTool`;
- registers in OpenJarvis `ToolRegistry`;
- executes through OpenJarvis `ToolExecutor`;
- receives ORION lease and trusted roots out of band;
- does not expose absolute trusted roots to the model;
- returns structured data that ORION converts into canonical `EvidenceEnvelope`.

## Next physical run

`V3-RUN-001`

It will verify on the owner's Windows PC:

1. OpenJarvis built-in `file_read` is present;
2. OpenJarvis built-in `file_write` is present;
3. the missing `orion_filesystem_search` extension is registered in OpenJarvis `ToolRegistry`;
4. real filesystem search executes through OpenJarvis `ToolExecutor`;
5. ORION Action Lease and trusted-root scope remain authoritative;
6. absolute trusted roots do not leak;
7. ORION normalizes the successful ToolResult into canonical evidence.

After this passes, continue donor-first capability qualification and evaluate/launch the pinned OpenJarvis desktop stack.

## Protected fallback

Legacy ORION remains available as the proven external transport/fallback.

Frozen fallback:
- repo: `Sadusor/Orion`
- branch: `checkpoint/2026-10-01-orion-remote-project-link`
- SHA: `327d32f714129ca633517a8f4158cd84820c1504`

Do not retire it until later V3 parity gates physically pass.
