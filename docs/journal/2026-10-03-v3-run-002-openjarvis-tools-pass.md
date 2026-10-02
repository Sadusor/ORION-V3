# V3-RUN-002 — donor-first OpenJarvis tool path

Date: 2026-10-03  
Status: **PHYSICAL PASS**

## Exact identities

ORION-V3:
`327ae8226c20f3b8d7dd0ef283dd87ac2f9addaf`

Pinned OpenJarvis:
`Sadusor/OpenJarvis@309a4f1044ccfb2032264832a31fef2f1d314586`

Legacy ORION Remote transport:
`237c3ee91c371f27454150c041c5b61432d97323`

ORION-V3 run:
`V3-RUN-002`

Legacy Remote transport record:
`attempt 402` — transport log only, not a V3 run number.

## Physical evidence

```text
V3_RUN_ID=V3-RUN-002
OPENJARVIS_FILE_READ_BUILTIN=FOUND
OPENJARVIS_FILE_WRITE_BUILTIN=FOUND
OPENJARVIS_CUSTOM_SEARCH_REGISTERED=PASS
REAL_FILESYSTEM_SEARCH=PASS
ABSOLUTE_TRUST_ROOT_HIDDEN=PASS
ORION_EVIDENCE_NORMALIZED=PASS
V31_OPENJARVIS_TOOLS=PASS
STATUS> PASS
```

Regression suite:
`16 passed`

## What this proves

1. OpenJarvis built-in filesystem tools are available in the pinned donor runtime.
2. ORION does not need a parallel Hands/tool framework.
3. A genuinely missing capability can be added as an OpenJarvis-native registered tool.
4. The custom search capability executes through OpenJarvis `ToolRegistry` + `ToolExecutor`.
5. ORION remains the authority through Action Lease validation and trusted-root bindings.
6. Absolute trusted filesystem roots are not exposed in the tool result.
7. ORION converts the donor ToolResult into canonical `EvidenceEnvelope`.

## Architecture decision

V3.1 execution rule is now physically validated:

```text
ORION authority/evidence
        ↓
OpenJarvis ToolRegistry / ToolExecutor
        ↓
reuse donor tool
OR
smallest missing OpenJarvis-native extension
```

Future execution capabilities must be inventoried in OpenJarvis/donors before custom implementation.
