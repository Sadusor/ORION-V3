# ORION V3 Modules

This directory contains replaceable, bounded product modules built under the **FREEZE RULE**.

## Local Brain

`local_brain.py` is the first connected product module.

Boundary:
- accepts owner text;
- talks only to loopback Ollama;
- prefers the local Qwen 3.5 9B model;
- returns advisory conclusion/draft text;
- owns no tools, Hands, capabilities, approval, execution, STOP, memory promotion, filesystem access, browser access, or cloud access.

The product server is only a narrow transport/state hook. STRATA has one small presentation hook that prints a completed `brain_conclusion` into the existing chat exactly once; it adds no new authority or route.

The first qualification gate proves:

`Ask ORION -> LocalBrainModule -> Ollama/Qwen -> brain_conclusion -> STRATA UI`

Nothing executes in this gate.

## Donor decision

The transport mechanics follow the proven legacy ORION Local Brain contract:
- loopback-only Ollama;
- `/api/tags` model discovery;
- `/api/generate`;
- explicit JSON schema;
- `think: false`;
- temperature 0;
- bounded token generation.

OpenJarvis remains the preferred future replaceable engine substrate, but importing its larger runtime for this first single-model seam would widen the dependency and regression surface without adding authority or functionality needed by this gate.


## Verifier + Preflight

`verifier_preflight.py` adds the second bounded gate after Local Brain.

It performs:
- deterministic preflight for executable mechanics or false claims that actions already happened;
- a second structured local-model verification pass for unsupported claims and missing evidence;
- fail-closed blocking when the verifier cannot complete.

`brain_pipeline.py` composes the already-proven Local Brain with this verifier without modifying `local_brain.py`.

Authority boundary:
- verifier may PASS/BLOCK advisory text only;
- it cannot execute;
- it cannot grant approval;
- it cannot call Hands;
- it cannot browse, inspect files, write memory, or contact cloud models.

The product-server hook remains the same `LOCAL_BRAIN.start()/view()` interface.
