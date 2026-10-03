# ORION V3 Donor Map

This carries forward the original ORION donor research. Presence here is not adoption.

## Foundation / control substrate

| Donor | Role | V3 disposition |
|---|---|---|
| OpenJarvis | registries, ToolRegistry/ToolExecutor, built-in filesystem/browser/web/shell/patch tools, engines, provider routing, channels, events, skills, UI/runtime | **ADOPTED REPLACEABLE SUBSTRATE** |
| Jev Harness | proposal -> evidence -> code decides -> host authorizes | ADAPT CONCEPT |
| WORKSHOP | provider discovery, role mappings, health, fallbacks, safe serialization | ADAPT / BENCHMARK |
| OpenMuse | durable task worker, SQL leases, checkpoints, pause/resume/cancel, idempotent receipts, bounded model-loop and isolated-computer patterns | **MIDDLE-LAYER / DURABILITY DONOR** |

## Execution Hands

| Donor | Role | V3 disposition |
|---|---|---|
| CUA | bounded Computer Hand/browser substrate, semantic UI, effect verification | SPIKE FIRST |
| Aegis | hardened browser containment | CONTROL / REUSE PROVEN IDEAS |
| PinchTab | semantic browser refs, narrow grants, revocable sessions | BROWSER CHALLENGER |
| OpenBot | human takeover, scoped secret entry, governed computer patterns | ADAPT |
| Artemis | Android/device Hand | PRIMARY DEVICE CANDIDATE |
| software-agent-sdk / OpenHands | semantic Coding Hand plus strong editor/terminal primitives; heavy dependency surface | **SEMANTIC CODING-HAND CANDIDATE** |
| Claude Code | mature semantic Coding Hand / capability baseline | **SEMANTIC CODING-HAND CANDIDATE** |
| ACP / python-sdk | coding/session protocol | ADAPT |
| n8n | commodity connectors/workflows | ADAPTER CANDIDATE |
| OpenSandbox | isolation/runtime | BENCHMARK |

## Perception / computer reasoning

| Donor | Role | V3 disposition |
|---|---|---|
| UI-TARS | GUI grounding/reasoning | BENCHMARK |
| UI-TARS Desktop | GUI runtime/operator | BENCHMARK |
| Qwen vision | local visual reasoning | BENCHMARK / EXISTING EVIDENCE |

## Memory / context

| Donor | Role | V3 disposition |
|---|---|---|
| KnowledgeOS | evidence/provenance, retrieval traces, index compatibility | PRIMARY INTERNAL DONOR |
| agentmemory | retrieval/consolidation challenger | BENCHMARK |
| TencentDB-Agent-Memory | context/code memory challenger | BENCHMARK |
| OpenViking | memory/context architecture | REFERENCE / LICENSE-SENSITIVE |
| memanto | memory challenger | BENCHMARK |
| codebase-memory-mcp | code context | BENCHMARK |
| Graft | code context | BENCHMARK |
| Aider repo-map ideas | code context | REFERENCE |

## Browser read/extract

| Donor | Role | V3 disposition |
|---|---|---|
| Firecrawl | structured web extraction | SPECIALIST CANDIDATE |
| Scrapling | extraction/scraping | SPECIALIST CANDIDATE |
| browser-use | browser agent reference | PREVIOUS AUDITED REVISION REJECTED FOR PERMISSION BOUNDARY |

## Phone / channel / workflow UX

| Donor | Role | V3 disposition |
|---|---|---|
| KIRA | phone-PC transport patterns and OBSERVE->UNDERSTAND->DECIDE->VALIDATE->ACT->VERIFY loop | INTERNAL DONOR |
| Orion-Copilot | Android companion patterns | INTERNAL DONOR |
| PizzaBot | background-work / needs-you UX | REFERENCE |
| Orca | workflow/UX patterns | REFERENCE |

## Voice

| Donor | Role | V3 disposition |
|---|---|---|
| whisper.cpp | local STT | CANDIDATE |
| EchoFetch | transcription/audio workflow | CANDIDATE |
| openWakeWord | wake word | LATER CANDIDATE |
| Kokoro | TTS | CANDIDATE |

## Evaluation / routing

| Donor | Role | V3 disposition |
|---|---|---|
| LLMRouterBench | router qualification | BENCHMARK |
| Ai-Benchmark-v4 | model/router evaluation | BENCHMARK |
| cua-bench | computer-use trajectories/effect verification | BENCHMARK |

## Audit / research-only

| Donor | Role | V3 disposition |
|---|---|---|
| Buzz | provenance/audit conceptual donor | REFERENCE |
| OBLITERATUS | unsafe-model research | RESEARCH ONLY / NEVER RUNTIME AUTHORITY |

## Donor adoption rule

For each subsystem:
1. define the ORION-owned contract;
2. identify strongest donors;
3. test the riskiest assumption first;
4. pin revision/license/evidence;
5. adapt behind ORION semantics;
6. preserve an exit path.

Borrow capability, not ownership.

## Tool reuse rule

OpenJarvis is the default execution/tool substrate after Gate 1.

Before creating any new ORION execution capability:
1. inspect `ToolRegistry` and built-in OpenJarvis tools at the pinned donor revision;
2. reuse the donor tool if it satisfies the ORION contract;
3. wrap it only as needed for ORION Action Leases, trusted bindings, evidence and Stop;
4. if the capability is genuinely absent, implement the smallest OpenJarvis-native registered extension;
5. never create a parallel ORION tool/Hand registry merely for convenience.

V3.1 audit result:
- `file_read`: present upstream;
- `file_write`: present upstream;
- `filesystem.search` exact-basename capability: not found upstream at the pinned revision, so it is the first justified custom registered extension.


## V3-RUN-002 physical result

The donor-first execution rule is physically proven on Windows.

- OpenJarvis `file_read`: FOUND
- OpenJarvis `file_write`: FOUND
- custom exact-basename search: registered as OpenJarvis-native extension
- OpenJarvis ToolExecutor execution: PASS
- ORION authority/trusted-root enforcement: PASS
- ORION evidence normalization: PASS

See:
`docs/journal/2026-10-03-v3-run-002-openjarvis-tools-pass.md`

## 2026-10-03 donor-role correction

Donors are no longer evaluated as candidates to replace ORION wholesale.

- **OpenJarvis** supplies infrastructure/tool/workflow/frontend pieces.
- **OpenMuse** is especially relevant for durable task execution: leases,
  checkpoints, pause/resume/cancel, receipts and isolated-computer patterns.
  It is not ORION's semantic/policy router.
- **OpenHands / Claude Code** may be used as high-level semantic Coding Hands
  so ORION does not rebuild internal coding command sequences.
- **jarvis.institute** remains product/UX inspiration only; the actual product
  source is proprietary and must not be confused with Stanford OpenJarvis.
- **KnowledgeOS/memory donors** are now early-core work because canonical
  continuity is a primary ORION problem, not a late enhancement.

Capability harvesting should prefer existing proven legacy ORION Remote
mechanics, donor implementations and native Windows APIs before custom code.
