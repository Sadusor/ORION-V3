# V3-RUN-044A — 9B thinking-ON qualification staged

Date: 2026-10-04

## Purpose

Run one final controlled local-governor check before production attachment.

This is not a new model tournament.

Candidate:
- `qwen35-9b-orion:latest`
- reasoning/thinking: ON (`reasoning_effort=medium`)
- context: 4096

## Workload

Reuse the exact five harder behavioral cases from V3-RUN-043:
1. MULTI_STEP
2. TRANSIENT_RECOVERY
3. APPROVAL_RESUME
4. CLOUD_ESCALATION
5. STALE_AUTHORITY

The same seven-tool catalog and deterministic tool behavior are reused.

## Why

RUN-042 proved 9B thinking OFF was the fastest/lightest 4/4 daily-operator candidate.
RUN-043 proved that none of 9B OFF, IQ4 OFF, or IQ4 ON reached 5/5 on the harder tournament.

The detailed RUN-043 9B-OFF row was not preserved in the durable tail. Therefore this gate does not invent a missing OFF wall-time comparison.

It asks one narrow question:

> Does 9B thinking ON improve the harder behavioral qualification enough to justify changing the production governor setting before RUN-045?

## Semantics

Benchmark validity and model qualification remain separate:
- `STATUS> PASS` means the controlled run executed validly with thinking mapped ON and context verified at 4096.
- `NINE_B_THINKING_ON_QUALIFIED> PASS` means the model itself achieved 5/5.
- A valid benchmark may PASS even if the candidate is not behaviorally qualified.

## Safety

- local model only;
- no paid cloud request;
- deterministic benchmark tools only;
- no production approval authority is delegated to the model;
- V3-RUN-044 production control-plane PASS remains authoritative and unchanged.

## Next

After this one measurement, freeze 9B ON/OFF policy and proceed directly to V3-RUN-045 production-governor attachment.
