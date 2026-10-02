# ORION V3 Status

Updated: 2026-10-03

## Stage

OpenJarvis Foundation Gate 1 — **physical authority/executor slice passed; remaining falsifiers in progress**.

ORION-V3 is a completely separate repository from the proven ORION implementation.

## Current claims

- architecture: DOCUMENTED
- OpenJarvis substrate: CANDIDATE, not yet fully adopted
- Authority Boundary V0: IMPLEMENTED / UNDER PHYSICAL QUALIFICATION
- ORION authority unit contract: AUTOMATED PASS (16/16)
- OpenJarvis proxy compatibility contract: AUTOMATED PASS
- real pinned OpenJarvis + Windows authority/executor integration: **PHYSICAL PASS**
- native-agent/direct-bypass falsifier: NOT YET PHYSICALLY PASSED
- physical Stop falsifier: NOT YET PHYSICALLY PASSED
- old ORION Remote: proven external transport/fallback; architecture untouched

## Pinned OpenJarvis donor

`Sadusor/OpenJarvis@309a4f1044ccfb2032264832a31fef2f1d314586`

## Latest physical evidence

- ORION-V3 tested SHA: `98edcd5e018ad60cae18c8654bff289e69ab0e70`
- ORION Remote task SHA: `07e65bb00be29746b201bdeffead68ddcf9a4867`
- physical attempt: `397`
- result: **PASS**
- real OpenJarvis Rust extension: PASS
- authority tests: **16/16 PASS**
- no lease -> denied
- valid lease -> dispatcher reached
- trusted-binding override -> denied

Evidence:
`docs/journal/2026-10-03-gate1-openjarvis-physical-authority-pass.md`

Earlier evidence:
- `docs/journal/2026-10-03-gate1-authority-unit-result.md`
- `docs/journal/2026-10-03-gate1-openjarvis-proxy-contract-result.md`

## Current bounded task

Finish Gate 1 without widening scope beyond `filesystem.search`.

Next physical falsifiers:

1. native Jarvis/direct-tool bypass cannot reach the Hand without ORION authority;
2. Jarvis-side capability widening cannot override ORION denial;
3. deliberately blocking work can be physically stopped through an ORION-owned killable worker;
4. timeout alone never becomes STOPPED;
5. donor EventBus/session state remains non-canonical.

## Proven target flow so far

```text
owner intent
-> ORION issues bounded Action Lease
-> ephemeral lease-bound OpenJarvis proxy
-> Jarvis default-deny capability gate
-> ORION AuthorityGateway revalidates lease/scope/operation
-> deterministic dispatcher
```

The lease is not a model/tool argument and Jarvis cannot mint it.

## Protected fallback

- repo: `Sadusor/Orion`
- branch: `checkpoint/2026-10-01-orion-remote-project-link`
- SHA: `327d32f714129ca633517a8f4158cd84820c1504`

Do not modify or retire the fallback until V3 independently passes its later parity gates.
