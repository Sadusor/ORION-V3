# ORION V3 Status

Updated: 2026-10-03

## Stage

**Gate 1 COMPLETE — OpenJarvis accepted as ORION V3's preferred replaceable generic substrate.**

ORION-V3 remains a completely separate repository from the proven ORION implementation.

## Current claims

- architecture: DOCUMENTED
- OpenJarvis substrate: **ADOPTED AS REPLACEABLE SUBSTRATE**
- ORION remains sole authority: **PHYSICALLY PROVEN for Gate-1 scope**
- Authority Boundary V0: **PHYSICAL PASS**
- ORION authority unit contract: **AUTOMATED PASS (16/16)**
- real pinned OpenJarvis + Windows integration: **PHYSICAL PASS**
- native Jarvis bypass falsifier: **PHYSICAL PASS**
- Jarvis policy widening falsifier: **PHYSICAL PASS**
- timeout != Stop falsifier: **PHYSICAL PASS**
- ORION-owned killable worker Stop: **PHYSICAL PASS**
- old ORION Remote: preserved as proven transport/fallback

## Exact Gate-1 completion evidence

ORION-V3:
`dc13d5caddf2489879b2d300addaa5419b3d5975`

OpenJarvis:
`Sadusor/OpenJarvis@309a4f1044ccfb2032264832a31fef2f1d314586`

ORION Remote task:
`df4ef699706ede0ce6d9de34eaeb74b84213a116`

External Remote transport record:
`attempt 399` — **transport log only; not an ORION-V3 attempt number**

Result:
**PASS**

Observed:
- no lease -> denied;
- valid lease -> dispatch;
- trust-binding override -> denied;
- native ReAct bypass -> denied;
- permissive Jarvis policy -> still no ORION authority;
- donor timeout returned while work continued;
- actual worker PID terminated;
- Windows reported worker PID absent;
- heartbeat stopped;
- only then physical Stop passed.

Evidence:
`docs/journal/2026-10-03-gate1-complete.md`

## Authority hierarchy

```text
OWNER > ORION AUTHORITY > OpenJarvis SUBSTRATE > HANDS
```

OpenJarvis may narrow execution further but may not mint ORION authority.

## ORION-V3 run numbering

ORION-V3 uses its own run IDs beginning with `V3-RUN-001` in V3.1. Old ORION Remote attempt numbers are external transport evidence only and are never counted as ORION-V3 development attempts.

## Next bounded stage — V3.1 deterministic Hands

Start with real filesystem capability:

1. `filesystem.search`
2. `filesystem.list` as a separate operation
3. `filesystem.reveal` as a separate operation

Requirements:
- each operation gets its own lease;
- trusted roots remain ORION-owned;
- no shell fallback for ordinary file operations;
- real result evidence is normalized by ORION;
- Stop uses an ORION-owned killable worker boundary where cancellation matters.

After the first real Hand passes, evaluate/launch the pinned OpenJarvis desktop stack for UI/substrate harvesting under ORION governance.

## Protected fallback

- repo: `Sadusor/Orion`
- branch: `checkpoint/2026-10-01-orion-remote-project-link`
- SHA: `327d32f714129ca633517a8f4158cd84820c1504`

Do not retire the fallback until later V3 parity gates physically pass.
