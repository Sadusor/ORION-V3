# ORION V3 Status

Updated: 2026-10-03

## Stage

Bootstrap / OpenJarvis Foundation Gate 1.

ORION-V3 is a completely separate repository from the proven ORION implementation.

## Current claims

- architecture: DOCUMENTED
- OpenJarvis substrate: CANDIDATE, not adopted
- Authority Boundary V0: DRAFT
- ORION authority unit contract: AUTOMATED PASS (16/16)\n- OpenJarvis/Windows Gate-1 integration: NOT TESTED
- old ORION Remote: frozen external fallback; untouched

## Pinned OpenJarvis donor

`Sadusor/OpenJarvis@309a4f1044ccfb2032264832a31fef2f1d314586`

## Latest evidence\n\n`docs/journal/2026-10-03-gate1-authority-unit-result.md`\n\n## Current bounded task

Prove one operation only: `filesystem.search`.

Target flow:

semantic intent -> OpenJarvis ORION proxy -> ORION Action Lease validation -> deterministic filesystem search Hand -> normalized evidence -> verifier

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