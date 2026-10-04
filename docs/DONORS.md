# ORION V3 Donor Map

This carries forward the original ORION donor research. Presence here is not adoption.

## Foundation / control substrate

| Donor | Role | V3 disposition |
|---|---|---|
| OpenJarvis | registries, engines, provider routing, channels, events, skills, UI/runtime | GATE-1 PRIMARY |
| Jev Harness | proposal -> evidence -> code decides -> host authorizes | ADAPT CONCEPT |
| WORKSHOP | provider discovery, role mappings, health, fallbacks, safe serialization | ADAPT / BENCHMARK |

## Execution Hands

| Donor | Role | V3 disposition |
|---|---|---|
| CUA | bounded Computer Hand/browser substrate, semantic UI, effect verification | SPIKE FIRST |
| Aegis | hardened browser containment | CONTROL / REUSE PROVEN IDEAS |
| PinchTab | semantic browser refs, narrow grants, revocable sessions | BROWSER CHALLENGER |
| OpenBot | human takeover, scoped secret entry, governed computer patterns | ADAPT |
| CLI-Anything | deterministic agent-facing CLI Hands, JSON receipts, real-backend verification, preview/trajectory bundles | HIGH-PRIORITY HANDS DONOR / PROBE FIRST |
| Artemis | Android/device Hand | PRIMARY DEVICE CANDIDATE |
| software-agent-sdk / OpenHands | Coding Hand | ADAPTER CANDIDATE |
| Claude Code | Coding Hand | ADAPTER CANDIDATE |
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
| OpenMuse | frozen proposal hashes, approval binding, idempotent execution, receipts, uncertain-outcome semantics | HIGH-PRIORITY AUTHORITY/EXECUTION DONOR |
| Octop | tool guards, HITL policy, plugin registry, remote surfaces, ACP adapters | SECURITY/PLUGIN/REMOTE DONOR; REJECT AGENT AUTHORITY |

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
## Recent fork review — 2026-10-04

- CLI-Anything: test Hand/evidence contract patterns before adopting anything.
- OpenMuse: adapt exact-hash approval and one-shot/idempotent receipt patterns.
- Octop: study security/tool/plugin/remote patterns only; ORION remains authority.
- GhostTrack: no ORION runtime value found; no license reported; do not adopt.

See `docs/decisions/0003-donor-contract-patterns.md`.
