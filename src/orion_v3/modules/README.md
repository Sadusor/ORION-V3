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

The product server is only a narrow transport/state hook.

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
