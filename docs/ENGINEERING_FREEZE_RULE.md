# FREEZE RULE — Proven Core + Replaceable Modules

Status: **OWNER DIRECTIVE / ORION ENGINEERING INVARIANT**

Shorthand: **FREEZE RULE**

## Principle

ORION is designed around replaceable components. Its engineering process must match that architecture.

The default development sequence is:

```text
prove -> freeze exact commit -> branch from frozen state -> add isolated module -> test -> physical PASS -> freeze again
```

## Required behavior

1. **Proven code is read-only by default.**
   Once a capability is physically or contractually proven, preserve its exact commit and do not modify unrelated code while adding the next capability.

2. **New work is module-first.**
   Prefer new adapters, providers, Hands, connectors, importers, memory backends, UI adapters or other bounded modules over edits to existing proven internals.

3. **Use the smallest stable hook.**
   Existing core code may be touched only where a narrow interface is genuinely required. No incidental refactors or cleanup.

4. **Authority boundaries must remain stable.**
   New modules may not acquire ORION authority merely because they are connected.
   ORION continues to own policy, approvals, leases, canonical Task/Event truth, evidence verification, Stop/recovery truth and canonical Memory promotion.

5. **Optional modules must be detachable.**
   ORION must continue to work if an optional donor, Hand, connector, learning source, UI adapter or provider is absent/offline.
   External products must also remain independent of ORION unless an explicit product contract says otherwise.

6. **Freeze before extending.**
   Before substantial work, identify the latest proven baseline. Work on a feature branch derived from that baseline, not by repeatedly rewriting proven production code.

7. **Bound the diff.**
   State allowed files/modules before editing. Anything outside that scope requires separate owner approval.

8. **Qualify before merge.**
   Use isolated/unit/contract tests first, then relevant end-to-end or physical qualification. Do not declare a new baseline until the owner confirms PASS where physical behavior matters.

9. **PASS creates the next baseline.**
   Create a frozen branch at the exact passing commit. Future modules start there.

10. **Failed experiments are disposable.**
    Drop/revert the experimental module rather than spreading compensating changes through the core.

## TheHands application

TheHands follows the same rule.

Latest owner-confirmed TheHands baseline at the time this rule was adopted:

- `frozen/2026-10-06-manual-ps-pass`
- `0ed1064468001b155826bcf01d6cd11bf35852fa`

ORION integrations with TheHands must prefer external/read-only adapters and narrow module seams. Do not modify unrelated TheHands product code.

## Owner shorthand

When the owner says:

**FREEZE RULE**

interpret it as:

> Preserve all proven code. Branch from the latest frozen PASS. Build the requested capability as an isolated, replaceable module. Touch existing code only for the smallest necessary hook. Make no unrelated changes. Test it independently, then freeze the next physical PASS.

This is a standing engineering invariant.
