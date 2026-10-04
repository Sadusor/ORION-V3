# ORION V3 Status

Updated: 2026-10-04

## Stage

Bootstrap / OpenJarvis Foundation Gate 1.

ORION-V3 is a completely separate repository from the proven ORION implementation.

## Current claims

- Evidence Pack concurrency repair: PASS (`aee352d7f379`)
- Local Model Tournament Reasoning V2: PASS (`2e43a124646f`) — Qwen 3.5 9B ORION won FAST and THINKING
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

Local Model Tournament Reasoning V2 physically PASS. Qwen 3.5 9B ORION remains the leading general local interpreter; Gemma 4 12B is the closest challenger. No model passed every critical case, so deterministic ORION policy remains mandatory. Next model gates are role-specific rather than another generic tournament: Personal-vs-Project concurrency, coding/project-coordinator quality, and exact-runtime vision/personal-file retrieval. UI work can use STRATA as the V3 foundation with multi-lane extensions.

## Newly documented owner direction

- Multi-lane assistant architecture: Personal/Desktop Assistant remains available while project/coding workflows run.
- One physical model with isolated contexts or two different local models are both allowed; role assignment will be benchmark-driven.
- Add a post-tournament concurrency benchmark instead of assuming small local models are a resource bottleneck.
- Personal learning starts with ORION-owned retrieval over approved files, downloads, exports, screenshots and project data.
- Optional later LoRA/QLoRA personalization uses curated owner-approved examples; base model remains immutable and adapters remain replaceable.
- Vision is a first-class Personal Assistant requirement, but must be physically proven on the exact installed model/runtime.
- No automatic whole-PC scraping or automatic training from credentials/private data.

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