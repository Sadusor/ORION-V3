# Autonomous Work Loop V1 — Module Boundaries

Status: **STAGED CONTRACT / NOT PHYSICALLY QUALIFIED**

## Why these modules exist

Split only where replacement/security/testing boundaries are real. Tiny logic remains together.

| Module | Owns | Must not own |
|---|---|---|
| contracts | typed proposal/evidence/state vocabulary | execution, policy |
| paths | deterministic path preflight | OS sandbox |
| policy | GREEN/YELLOW/RED decision from concrete proposal properties | model reasoning, execution |
| authorization | exact proposal/time-bound authorization | owner identity UI, execution |
| verifier | evidence binding/type/revision validation | running tests |
| vault | current project state + journal persistence | ORION Memory |
| engine | deterministic transition coordination | Qwen, Hands, STOP implementation |
| executor | Work Hand boundary interface | authority |
| dry_run | pre-sandbox no-write simulation | PASS claims |
| owner_input | future owner instruction source interface | chat storage |
| stop | adapter contract to existing ORION STOP | a second STOP |
| observer | real event projection | fake thinking/progress |
| sandbox_srt | SRT config planning only | SRT install/run/qualification |

## Dependency direction

```text
UI / CLI / future Work Chat
        |
        v
owner_input -----> engine <----- observer
                    |
          +---------+---------+
          |         |         |
        policy    vault    verifier
          |                   |
        paths              evidence
          |
   authorization
          |
       executor
          |
   qualified sandbox
          |
       TheHands
```

Qwen is outside the authority core: it produces a Proposal. The engine/policy decide whether that proposal may progress.

## Frozen/reuse rule

Do not merge these modules into Memory V1/V1.1 or frozen TheHands. Integration occurs through adapters. If physical testing proves two adjacent modules add no useful boundary, owner may approve combining them rather than preserving architecture for its own sake.
