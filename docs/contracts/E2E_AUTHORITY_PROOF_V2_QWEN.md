# E2E Authority Proof V2 — Qwen Language Boundary

Date: 2026-10-04  
Status: PREPARE/FREEZE STAGED  
Legacy Remote UI: FROZEN / UNCHANGED

## Purpose

Prove that a replaceable local Qwen 9B model can understand a normal owner request and translate it into a bounded proposal while ORION remains the sole authority plane.

Proof V1 already proved hostile-scope rejection, exact-hash approval binding, mutation denial, deterministic execution, independent verification, and provenance. V2 keeps those authority mechanics and inserts Qwen only before ORION canonicalization.

## Owner-language goal

Create a tiny proof text file named `ORION_E2E_TEST.txt` containing exactly `ORION END TO END PASS` followed by one newline, and don't change anything else.

## Required role separation

- OWNER: supplies the natural-language goal and later approves the exact frozen runtime plan hash.
- QWEN 9B: interprets language only; advisory; thinking enabled for this proof; no approval or execution authority.
- ORION: validates the interpretation, resolves the disposable approved root, adds policy-owned deny fields, canonicalizes the executable contract, freezes/hash-binds it, and dispatches only after exact owner approval.
- HAND: writes the exact approved file and returns a machine receipt.
- VERIFIERS: independently inspect final deterministic evidence; their prose cannot override deterministic mismatches.

## Prepare phase

The staged prepare task must:

1. demand-start local Ollama only if required;
2. dynamically select an installed local Qwen 9B model, preferring the ORION-tuned 9B model;
3. send the owner-language goal with `think=true` and temperature 0;
4. require a tiny interpretation schema: `action`, `filename`, `content_utf8`;
5. reject unknown/missing/wrong interpretation fields;
6. let ORION construct the full executable contract, including `network=denied` and `extra_writes=denied`;
7. bind the frozen plan to the owner-goal SHA-256, interpreter model, and interpreter-proposal SHA-256;
8. perform no Hand write;
9. publish the exact `FROZEN_PLAN_SHA256`;
10. stop awaiting owner approval of that exact hash.

## Execute phase

Only after the owner explicitly approves the exact V2 runtime plan hash may the execution task be staged.

Execution reuses the V1 authority gates:

- exact approval hash binding;
- post-approval mutation denial;
- deterministic one-file Hand;
- idempotent replay;
- exact path/bytes/SHA verification;
- outside-scope untouched;
- no Hand network/credential use;
- machine-readable receipt;
- two independent verifier calls;
- deterministic gates override model claims;
- complete evidence/provenance record.

## PASS meaning

A V2 PASS proves:

`owner natural language -> Qwen proposal -> ORION canonical contract -> exact owner approval -> deterministic Hand -> evidence -> independent verification`

It does not grant Qwen authority and does not prove general autonomous competence.

## After PASS

Begin the new V3 phone UI alpha before the broad Hands/substrate tournament.

The new UI target is one request for low-risk actions, at most one compact confirmation for bounded writes, explicit confirmation for high-risk actions, automatic state refresh, global STOP, and inline evidence.


## Thinking-mode decision

Owner requirement: keep Qwen thinking enabled when the quality gain is worth the modest latency increase.

Therefore Proof V2 must be rerun with Qwen thinking ON before any execution hash is approved. The earlier prepare PASS with thinking OFF remains valid evidence of the off-mode path, but its frozen plan hash is superseded and must not be executed.

The canonical V2 plan now records `interpreter_thinking: true` so the approved runtime hash also binds the chosen reasoning mode.
