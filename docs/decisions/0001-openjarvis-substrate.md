# ADR-0001 — OpenJarvis as Preferred Substrate Candidate

Status: ACCEPTED FOR FALSIFICATION, NOT ADOPTED
Date: 2026-10-03

## Context

ORION was about to recreate generic registry, event, tool-execution and provider infrastructure.
Source inspection showed OpenJarvis already implements much of that substrate.

## Decision

ORION V3 will physically test OpenJarvis as the preferred generic substrate.

Hierarchy:
ORION authority -> OpenJarvis substrate -> Hands

OpenJarvis security stays active as a narrow-only defense layer and uses default-deny on ORION paths.

## Explicitly not decided

We are not:
- renaming OpenJarvis into ORION;
- letting Jarvis autonomous agents become the ORION orchestrator;
- storing canonical Task/Event truth in Jarvis sessions;
- letting Jarvis memory become canonical Memory;
- treating registration as permission;
- treating timeout as Stop.

## Risks under test

- authority leakage;
- duplicate security systems;
- duplicate state/memory;
- upstream semantic drift;
- insufficient Stop semantics.

Gate 1 exists to falsify these risks.

## Revisit

If Gate 1 fails a fundamental authority invariant, OpenJarvis returns to donor/reference status.