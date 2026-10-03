# V3-RUN-036 — environment composition failure; operator not tested

Date: 2026-10-04

Status: **PHYSICAL FAIL — ARCHITECTURE BENCHMARK NOT REACHED**

Remote source SHA:
`3b4b81eeefa512702b607e12d7511a19a6f7e6e0`

Session:
`8ae6e0d5049d`

## Physical result

Preflight and V3 regression passed:
- authoring preflight: PASS
- V3 regression: **131 passed in 8.52s**
- pinned OpenHands SDK: PASS

The mixed operator script then failed before any Qwen case ran:

`ModuleNotFoundError: No module named 'openjarvis_rust'`

Call chain:
- RUN-036 constructed OpenJarvis `CapabilityPolicy`;
- pinned OpenJarvis CapabilityPolicy imports its Rust bridge;
- the benchmark was running inside the OpenHands uv environment;
- that environment does not contain `openjarvis_rust`.

Therefore:
- Qwen mixed-tool routing: **NOT TESTED**
- search/status/edit/denial cases: **NOT REACHED**
- no operator score can be assigned.

## Smallest correction

Pinned OpenJarvis `ToolExecutor` accepts `capability_policy=None`.

The real ORION/OpenJarvis search tool already enforces:
- ORION Action Lease;
- ORION AuthorityGateway;
- trusted root binding;
- scope and argument validation.

RUN-036R therefore keeps:
- real OpenJarvis ToolRegistry;
- real OpenJarvis ToolExecutor;
- real ORION lease/gateway;
- real OpenHands FileEditor;
- ORION-native Capability Registry tool.

It removes only the optional OpenJarvis CapabilityPolicy object from the
combined OpenHands Python process, avoiding the Rust-extension dependency.

This is a benchmark-composition correction, not a production claim that donor
RBAC is unnecessary. The OpenJarvis-native policy path was already physically
proven separately in V3-RUN-002.

## V3-RUN-036R

Exact V3 SHA:
`f3e872c194e732a439fb36e8f21d77a03fd1a782`

Remote staging SHA:
`a9f15a6eaa92a096c8440c704d488c3e18c113a2`

Same four operator cases and same scoring as RUN-036.
