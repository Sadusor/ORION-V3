# ORION V3 Status

Updated: 2026-10-04

## Stage

Bootstrap / OpenJarvis Foundation Gate 1.

ORION-V3 is a completely separate repository from the proven ORION implementation.

## Current claims

- Evidence Pack concurrency repair: PASS (`aee352d7f379`)
- E2E Authority Proof V1: PASS (prepare `71c7f7cbccb3`, execute `9c623d9e5be6`)
- Donor contract probe: PASS (session `92c002cdf162`)
- architecture: DOCUMENTED
- OpenJarvis substrate: CANDIDATE, not adopted
- Authority Boundary V0: DRAFT
- Gate-1 runtime: NOT TESTED
- old ORION Remote: frozen external fallback; untouched

## Pinned OpenJarvis donor

`Sadusor/OpenJarvis@309a4f1044ccfb2032264832a31fef2f1d314586`

## Current bounded task

Qwen Thinking ON vs OFF - Reasoning V2 physically PASS at source `b4016372556db0005123b53b136b2fb0275fb115`, session `05f36317dcc8`. Result supports an adaptive policy rather than always ON: OFF was 23/36 critical passes at 1.649 s median; ON was 25/36 at 9.274 s median. Some classes require ON, while path-scope and cloud-approval provenance were unreliable in both modes and must remain behind deterministic ORION checks / stronger-model or human escalation. Next bounded step: owner acceptance of adaptive-thinking policy, then re-freeze Proof V2 using the selected mode for its simple exact bounded-write request before execution.

## Gate-1 attacks

1. no lease;
2. forged lease;
3. expired lease;
4. wrong operation or scope;
5. native Jarvis agent direct invocation;
6. side-effect tool outside ORION profile;
7. Jarvis policy accidentally open-by-default;
8. Jarvis capability widening while ORION denies;
9. model attempts to inject trusted roots;
10. blocking operation plus Stop;
11. donor telemetry mistaken for canonical state.

## Protected fallback

- repo: `Sadusor/Orion`
- branch: `checkpoint/2026-10-01-orion-remote-project-link`
- SHA: `327d32f714129ca633517a8f4158cd84820c1504`