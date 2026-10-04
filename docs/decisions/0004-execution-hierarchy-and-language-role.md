# Decision 0004 — Execution hierarchy and language role

Date: 2026-10-04  
Status: OWNER-APPROVED DIRECTION  
Execution authorization: NONE IMPLIED

## Decision

ORION remains a non-agent authority/control plane.

Natural-language understanding and open-ended reasoning belong to replaceable models. The leading local interpretation/manager candidate is Qwen 9B.

Execution should prefer the narrowest deterministic mechanism that can complete the approved task:

1. native deterministic ORION Hand;
2. specialist CLI Hand (including CLI-Anything-derived adapters where they pass ORION qualification);
3. full computer-use / agent substrate only when no narrower deterministic Hand is sufficient.

Full agents are fallback execution substrates, not the foundation of ORION authority.

## Role split

OWNER
- defines goals;
- approves exact bounded plans;
- retains final authority.

Reasoning models
- understand natural language;
- brainstorm, propose, critique and translate goals into structured candidate intents/plans;
- never self-authorize.

ORION
- understands structured contracts, not free-form intent;
- validates identity, scope, permissions, approval hash, task state, STOP, provenance and evidence requirements;
- dispatches only approved operations;
- remains the sole authority plane.

Hands
- execute only the exact frozen operation;
- do not widen scope;
- return machine-readable receipts and evidence.

## Qualification sequence

1. E2E Authority Proof V1: cloud reasoning + ORION + deterministic Hand + hostile scope probe + independent verification.
2. E2E Authority Proof V2: add Qwen 9B as the natural-language interpretation/proposal layer while preserving the same authority contract.
3. Freeze the core authority/approval/evidence contract after both proofs pass.
4. Run an execution tournament using the same bounded contracts:
   - native deterministic Hands;
   - qualified CLI/specialist Hands;
   - OpenHands/OpenJarvis/CUA-style heavier substrates.
5. Compare speed, CPU/GPU/power, reliability, evidence quality and boundary compliance.
6. Expand the specialist Hand library only from physically qualified adapters.
7. Build the new UI around the now-stable concepts. The frozen legacy Remote UI remains untouched.

## Why

This preserves the low-consumption goal while keeping powerful execution available when needed.

It prevents a language model or execution substrate from becoming ORION's authority.

It also makes every major component replaceable:
- language model;
- Hand adapter;
- computer-use substrate;
- memory implementation;
- UI.

## Non-decision

This owner approval confirms the architecture direction only.

It does not authorize execution of `docs/contracts/E2E_AUTHORITY_PROOF_V1.md`.
That proof still requires explicit owner approval of the exact contract before a runnable task is staged.
