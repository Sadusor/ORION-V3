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

Run `Local Model Tournament - Download + Benchmark` from Orion source `438791c52b19d03e037a629f5abb092395593f13`. One approved Remote run preflights disk space, downloads missing official Ollama-library challengers, then runs the same 12-case Reasoning V2 benchmark with three repetitions. Candidates: existing qwen35-9b-orion baseline, Gemma 2 9B, Gemma 4 12B, Llama 3.1 8B, Ministral 3 8B, Phi-4 Mini 3.8B, and Granite 4 Tiny-H 7B/A1B. Qwen and Gemma 4 also run their thinking modes. NVIDIA Nemotron Nano 9B V2 is excluded from auto-pull until an official/qualified Ollama-compatible quant source is approved. Benchmark has no Hand dispatch; only intended side effect is model downloads.

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