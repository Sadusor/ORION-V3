# ORION V3 — Contributor / AI Instructions

This file is authoritative for work in `Sadusor/ORION-V3`.

## Identity

ORION V3 is a clean experimental rebuild using mature donor infrastructure where it survives ORION authority contracts.
It is NOT the old ORION repository. Do not modify or retire the proven old Remote while V3 is experimental.

## Authority hierarchy

OWNER > ORION AUTHORITY > SUBSTRATE / DONORS > HANDS

ORION always owns:
- canonical Task/Event truth;
- PermissionGrants and Action Leases;
- approvals;
- privacy and budgets;
- operation authorization;
- evidence normalization and verification;
- Stop/recovery truth;
- canonical Memory promotion;
- continuity/restart semantics.

No donor is a co-authority.

## OpenJarvis rule

Preferred substrate candidate: `Sadusor/OpenJarvis@309a4f1044ccfb2032264832a31fef2f1d314586`.

On ORION-governed paths:
- OpenJarvis capability policy is fail-closed / default-deny;
- Jarvis security may only narrow authority, never create ORION authority;
- autonomous Jarvis agents do not receive unrestricted side-effect tools;
- EventBus is telemetry/transport, never canonical Task/Event truth;
- Jarvis timeout is NOT ORION Stop.

## Mandatory donor gate

Before substantial custom implementation:
1. classify the ORION layer;
2. inspect internal/proven ORION mechanics;
3. inspect serious donors;
4. **inventory the pinned OpenJarvis registry and built-in tools before writing any tool/Hand code;**
5. prefer configuring, adapting or wrapping an existing donor tool over reimplementing its capability;
6. compare security, Stop, evidence, Windows behavior, license and replaceability;
7. run the smallest falsification spike;
8. record the result;
9. custom-build only when donors genuinely lack the capability or fail a real ORION contract.

A missing capability should normally be added as an OpenJarvis-native registered tool, not as a second ORION execution framework.

## Old ORION protection

Fallback reference only:
- repo: `Sadusor/Orion`
- branch: `checkpoint/2026-10-01-orion-remote-project-link`
- SHA: `327d32f714129ca633517a8f4158cd84820c1504`

Do not push V3 experiments into that repository.

## Cost / supply chain

- Prefer local tests.
- No surprise paid APIs or hosted compute.
- No automatic GitHub Actions triggers without owner approval.
- Pin donor revisions used in physical gates.
- Do not execute downloaded donor installers/scripts merely because upstream says to.
- Never commit secrets, private logs or personal data.

## Public repository rule

ORION-V3 is currently public. Fixtures must be synthetic.

## Evidence labels

DOCUMENTED / GITHUB-CODED-UNVERIFIED / AUTOMATED PASS / PHYSICAL PASS / PARTIAL / FAIL / BLOCKED / NOT TESTED