# V3.1 architecture correction — reuse OpenJarvis tools

Date: 2026-10-03  
Status: DOCUMENTED / CODED — awaiting V3-RUN-001 physical test

## Correction

The first V3.1 draft started creating a parallel `orion_v3.hands` filesystem implementation.

That direction was rejected before physical execution because Gate 1 had already adopted OpenJarvis as the replaceable execution/tool substrate.

The corrected boundary is:

```text
OWNER
 -> ORION authority / Action Lease / trusted bindings / evidence / Stop truth
 -> OpenJarvis ToolRegistry + ToolExecutor
 -> existing OpenJarvis tool
    OR smallest registered extension only when upstream lacks the capability
```

## Pinned donor inventory

At `Sadusor/OpenJarvis@309a4f1044ccfb2032264832a31fef2f1d314586`:

- `file_read` exists and supports allowed-directory restrictions;
- `file_write` exists and supports allowed-directory restrictions;
- browser, web search, shell, patch, memory and other tools already exist;
- no dedicated exact-basename local filesystem-search tool was found in the pinned tool inventory.

Therefore V3.1 adds exactly one missing extension:
`orion_filesystem_search`.

It subclasses OpenJarvis `BaseTool`, is registered in OpenJarvis `ToolRegistry`, runs through OpenJarvis `ToolExecutor`, and receives ORION Action Lease + trusted-root bindings out of band.

## Explicit anti-reimplementation rule

Before any future tool/Hand implementation:
1. inventory OpenJarvis built-ins;
2. inventory relevant donors;
3. reuse existing capability if it satisfies the ORION contract;
4. wrap for ORION authority/evidence as necessary;
5. create new execution code only for a demonstrated capability gap.

## Run numbering

Old ORION Remote attempt numbers remain transport evidence only.

The corrected V3.1 physical sequence starts at:
`V3-RUN-001`.
