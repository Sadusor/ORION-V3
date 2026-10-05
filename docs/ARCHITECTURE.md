# ORION V3 Architecture

## North Star

ORION V3 is a persistent personal AI control plane assembled from replaceable mature components.

Stable principle: models think, Hands act, ORION authorizes/remembers/verifies/stops.

## Layering

Channels (PC / Phone / Voice)
-> Reasoning substrate (OpenJarvis engines, routing, registries)
-> ORION Authority Gateway
-> Replaceable Hands
-> Evidence
-> ORION Verifier
-> Canonical Task/Event state

## Models

Models may interpret intent, reason, critique and propose bounded operations.
Models may not mint permissions, widen leases, redefine scopes, declare effects successful, promote canonical Memory or redefine Stop truth.

## OpenJarvis substrate

Initial substrate candidate because it already supplies:
- typed registries;
- EventBus;
- model/engine abstractions;
- provider routing;
- channels;
- skills;
- speech/TTS;
- connectors;
- tool runtime;
- security defenses;
- desktop/UI infrastructure.

These are implementation mechanics, not ORION authority.

## ORION Authority Gateway

Every side-effecting ORION operation crosses one ORION authorization boundary.

An Action Lease binds at minimum:
- lease_id;
- task_id;
- operation_id;
- principal;
- scope;
- issued_at;
- expires_at;
- revocation state.

Future gates may bind exact argument hashes, approval descriptors and budgets.

## Defense in depth

Dispatch may proceed only when ORION allows AND the substrate allows.

Jarvis deny => no dispatch.
ORION deny => no dispatch.
Jarvis allow without ORION lease => no dispatch.

OpenJarvis CapabilityPolicy must use `default_deny=True` on ORION-governed paths.

## Hands

Stable operation names are ORION semantics; implementations remain replaceable.

Initial operations:
- filesystem.search
- filesystem.list
- filesystem.reveal
- project.publish

Future categories:
- browser.*
- computer.*
- coding.*
- android.*
- connector.*

## Evidence / verification

Hand output is not automatically success.
ORION normalizes evidence and an independent verifier decides acceptance.

Expected outcomes:
- confirmed
- unverifiable
- refused
- failed
- stopped
- blocked

## Stop

Timeout != Stop.
ORION reports STOPPED only after underlying owned work actually terminates or equivalent cancellation is verified.

## Memory

Canonical Memory remains ORION-owned.
Retrieval engines, vector stores, graphs and donor memory backends are derived/rebuildable.
Retrieved information never grants authority.

## UI and engineering control

The ORION product surfaces are separate STRATA/Claude-inspired PC and phone UIs. They consume ORION projections/connectors and are not engineering Remote parity rebuilds.

Manual engineering Remote execution is handled by `Sadusor/TheHands-`.

The older Remote stays frozen as emergency fallback only.

Build order: connectors -> PC + phone UI -> connect UI to backend/connectors -> physical qualification. Replacing or closing either product UI must not destroy Task/Event truth.

## Default routine flow

owner -> Qwen/local governor -> semantic intent -> ORION authorization -> deterministic/proven Hand -> evidence -> verifier

Hard/novel work may add a specialist AI before authorization, but one bounded Hand owns execution.