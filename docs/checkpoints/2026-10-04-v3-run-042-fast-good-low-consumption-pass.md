# V3-RUN-042 — fast + good + low-consumption decision benchmark PASS

Date: 2026-10-04

Status: **PHYSICAL PASS**

Remote source SHA:
`41934e96759d5b1374b59e8e63db99dbae55fdc3`

Session:
`8be7dbf86752`

Exact V3 SHA:
`d172b255f50aa2a5a289243f82db28c7fd072aad`

Common runtime:
- context = 4096 for every candidate;
- runtime context verified from Ollama /api/ps;
- every candidate cold-started after model unload;
- same bounded four-case mixed-tool ORION workload;
- correctness and authority remained hard gates.

All five candidates passed.

## Results

### 9B_OFF

Model:
`qwen35-9b-orion:latest`

- correctness: PASS
- actions: 6
- wall: 45.644 s
- peak GPU delta: 6420 MB
- peak RAM delta: 1461.8 MB
- Ollama processor: 100% GPU
- context: 4096
- runtime model bytes: 5,490,081,790
- runtime VRAM bytes: 5,490,081,790
- thinking: OFF

### 35B_OFF

Model:
`qwen3.6:35b-a3b`

- correctness: PASS
- actions: 4
- wall: 61.136 s
- peak GPU delta: 14529 MB
- peak RAM delta: 9770.6 MB
- Ollama processor: 39% CPU / 61% GPU
- context: 4096
- runtime model bytes: 22,483,965,047
- runtime VRAM bytes: 13,613,767,064
- thinking: OFF

### 27B_OFF

Model:
`qwen3.8:27b`

- correctness: PASS
- actions: 6
- wall: 168.155 s
- peak GPU delta: 13786 MB
- peak RAM delta: 6626.7 MB
- Ollama processor: 29% CPU / 71% GPU
- context: 4096
- runtime model bytes: 18,112,692,875
- runtime VRAM bytes: 12,813,703,575
- thinking: OFF

### IQ4_OFF

Model:
`batiai/qwen3.8-27b:iq4`

- correctness: PASS
- actions: 5
- wall: 84.393 s
- peak GPU delta: 14141 MB
- peak RAM delta: 2387.3 MB
- Ollama processor: 7% CPU / 93% GPU
- context: 4096
- runtime model bytes: 15,692,139,065
- runtime VRAM bytes: 14,549,421,914
- thinking: OFF

### IQ4_ON

Model:
`batiai/qwen3.8-27b:iq4`

- correctness: PASS
- actions: 5
- wall: 152.464 s
- peak GPU delta: 14148 MB
- peak RAM delta: 3157.2 MB
- Ollama processor: 7% CPU / 93% GPU
- context: 4096
- runtime model bytes: 15,692,139,065
- runtime VRAM bytes: 14,549,421,914
- thinking: ON (reasoning_effort=medium)

## Automatic benchmark winners

- fastest passing: 9B_OFF
- lowest peak RAM passing: 9B_OFF
- lowest peak GPU passing: 9B_OFF
- fewest actions passing: 35B_OFF

## Interpretation

For the intended ORION daily-local-operator goal — fast, correct and low
consumption — `qwen35-9b-orion:latest` is the current winner.

Against 35B:
- ~25% faster wall-clock;
- ~85% lower peak RAM delta;
- ~56% lower peak GPU-memory delta;
- fully GPU resident;
- same 4/4 correctness and zero authority bypasses.

Against Qwen3.8-27B:
- ~73% faster;
- ~78% lower peak RAM delta;
- ~53% lower peak GPU-memory delta.

Against IQ4 OFF:
- ~46% faster;
- ~39% lower peak RAM delta;
- ~55% lower peak GPU-memory delta.

The 9B used 6 agent actions versus 4 for 35B, so 35B is more action-efficient
on this tiny workload. Despite that, the 9B still finished materially faster.

IQ4 thinking ON produced no correctness advantage on this workload and increased
wall time from 84.393 s to 152.464 s while increasing RAM use. Thinking ON is
therefore not justified for the routine operator path from this evidence.

## Current recommendation

Default local ORION operator candidate:
`qwen35-9b-orion:latest`

Recommended mode:
- thinking OFF;
- context 4096 for routine operator work;
- bounded model-facing schemas;
- ORION authority enforcement remains independent.

Preferred heavier fallback:
`qwen3.6:35b-a3b`

Reason:
35B remained correct, used fewer actions, and was substantially faster than
Qwen3.8-27B on this machine.

Do not use Qwen3.8-27B or IQ4 as the default routine operator based on current
physical evidence.

## Limits of this decision

RUN-042 is a simple four-case mixed-tool smoke, not a full general-intelligence
ranking.

Before permanently freezing the 9B as the only local operator, it should still
be challenged on:
- multi-step tool chains;
- tool failure and recovery;
- approval/wait/resume;
- larger tool catalogs;
- cloud-AI routing;
- stale approval / forbidden-action restraint;
- longer real project tasks.

For daily lightweight routing, however, RUN-042 currently favors the 9B
decisively.
