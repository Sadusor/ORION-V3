# Decision 0017 — Freeze Proven Baselines and Extend Through Modules

Date: 2026-10-06  
Status: **ACCEPTED / OWNER DIRECTIVE**

## Decision

ORION V3 and TheHands use the **FREEZE RULE** as the default engineering method.

When a capability is physically proven working:

1. preserve the exact passing commit on a frozen branch;
2. treat that proven code as read-only by default;
3. start the next feature from the latest frozen PASS;
4. implement the new capability as an isolated, replaceable module/adapter whenever possible;
5. touch existing proven files only for the smallest necessary hook;
6. make no unrelated refactors, cleanup or redesign;
7. qualify the module independently and then through the smallest relevant integration/physical gate;
8. after owner-confirmed PASS, create the next frozen baseline.

A failed experimental module should be dropped or reverted rather than repaired by widening edits into unrelated proven code.

## Why

ORION's architecture already requires replaceable models, Hands, memory backends, connectors, providers and UI adapters. The development process must preserve the same replaceability.

Repeatedly modifying proven core code creates regression risk, obscures causality and can damage already-qualified operator paths.

Module-first development keeps:
- regression surface small;
- rollback simple;
- evidence attributable;
- optional integrations detachable;
- authority boundaries visible;
- frozen recovery points available.

## Scope discipline

Before implementation, state the bounded files/modules allowed to change.

Anything outside that set requires a separate justification and owner approval.

Protected proven subsystems may not be changed incidentally merely because a new feature touches the same product.

## TheHands

TheHands follows the same rule.

At adoption time its latest owner-confirmed physical baseline is:

`frozen/2026-10-06-manual-ps-pass`

at:

`0ed1064468001b155826bcf01d6cd11bf35852fa`

ORION integrations with TheHands must prefer narrow, optional module seams and must not make either product depend on the other unless the owner explicitly approves such a contract.

## Shorthand

The owner may invoke the entire rule by saying:

**FREEZE RULE**

Canonical operational detail: `docs/ENGINEERING_FREEZE_RULE.md`.
