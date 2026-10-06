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
4. compare security, Stop, evidence, Windows behavior, license and replaceability;
5. run the smallest falsification spike;
6. record the result;
7. custom-build only when donors fail a real ORION contract.


## FREEZE RULE — mandatory engineering method

**FREEZE RULE** is standing owner shorthand and an ORION engineering invariant.

It means:
- proven code is read-only by default;
- identify the latest frozen PASS before substantial work;
- branch from that proven state;
- implement new capability as an isolated, replaceable module/adapter first;
- touch existing core files only for the smallest necessary hook;
- make no unrelated refactor, cleanup or redesign;
- bound the allowed diff before editing;
- test the module independently before merge;
- owner-confirmed physical PASS creates the next frozen baseline.

A failed experiment is disposable. Drop/revert the experimental module rather than spreading compensating edits through proven core.

This applies to ORION and to engineering integrations with TheHands.

Canonical rule: `docs/ENGINEERING_FREEZE_RULE.md`.

## Manual engineering Remote

For owner-approved manual engineering execution, use `Sadusor/TheHands-`.

Default flow:

`GIT CHECK -> APPROVE & START -> STOP`

PowerShell 1 is MAIN; PowerShell 2-4 are independent additional slots.

Do not create new routine engineering task-routing machinery in the frozen fallback Remote. The older Remote remains emergency fallback only and must stay untouched.

Canonical decision: `docs/decisions/0016-thehands-primary-engineering-remote.md`.

If/when the real runtime is connected to TheHands lifecycle controls, follow `docs/contracts/THEHANDS_LIFECYCLE_BRIDGE.md`. Do not use demo/mock servers as lifecycle proof.

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