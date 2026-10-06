# DeepSeek deployment-block review — Canonical Memory Review + Promotion V1

Date: 2026-10-06  
Reviewed pre-hardening candidate: `9a2aafc02aa560a883237d4104e835ae0592d7eb`  
Reviewer verdict: **BLOCK DEPLOYMENT**

## Findings assessed

DeepSeek raised five concrete requirements before the first durable canonical-memory write could be installed live:

1. define and enforce a real promotion-authority boundary;
2. preserve source provenance/trust through promotion and avoid assistant -> owner trust inversion;
3. re-run safety filtering at promotion time, not only during low-trust conversation recall;
4. bind canonical content exactly to the candidate snapshot;
5. provide a non-destructive revocation path for a poisoned/wrong promoted memory.

Two of these were already true in the pre-hardening implementation:

- PROMOTE copied the exact candidate content/hash/provenance snapshot;
- canonical rows preserved the originating `trust_origin` and `trust_tier`.

However, the review correctly identified that those facts were not enough. The durable write endpoint relied on the same paired-token/loopback auth model as ordinary product routes, assistant-origin candidates could still be promoted, canonical promotion had only secret filtering (not instruction-like filtering), and V1 had no append-only revocation path.

## Changes applied before live installation

### 1. Promotion authority is now stricter than ordinary ORION routes

Durable review uses two authenticated server calls:

```text
real owner UI gesture
  -> POST /api/memory/review-ticket
  -> short-lived one-time server token bound to:
       candidate id
       candidate content SHA-256
       exact decision
       owner scope
       paired-device actor fingerprint
  -> POST /api/memory/decision with that token
```

Both routes require a **valid paired owner token even on loopback**.

The normal ORION rule that trusts PC-local loopback remains unchanged for other routes. Canonical-memory review deliberately does not inherit that exemption.

Review tickets:

- expire after 90 seconds;
- are kept in process memory only;
- are consumed exactly once;
- cannot be replayed;
- are bound to the exact candidate/hash/decision/actor.

This does not claim to protect against compromise of an already-paired owner token. In the ORION V1 threat model, possession of a paired owner token is owner-device authority. The added ticket prevents stale/replayed one-step promotion calls and keeps models/ordinary routes away from the durable write primitive.

### 2. Assistant-origin promotion is blocked in V1

Assistant candidates may remain queued, deferred, or rejected for evidence/review.

They **cannot** become canonical Memory.

The owner must restate a verified fact in an owner message and promote that exact owner-origin source instead.

This prevents a down-weighted assistant prior from silently becoming high-trust durable context.

### 3. Trust provenance remains immutable through promotion

Canonical records preserve:

- candidate id;
- exact content;
- exact content SHA-256;
- original source reference;
- original trust origin;
- original trust tier;
- complete candidate snapshot;
- promotion decision id/hash.

Promotion performs no summarization, paraphrase, or trust-tier upgrade.

### 4. Promotion-time safety filtering

PROMOTE re-evaluates the exact candidate content under the canonical-memory boundary.

Blocked in V1:

- private-key material;
- password/api-key/secret/token assignments;
- Bearer authorization values;
- obvious stored prompt-injection patterns;
- system/developer override language;
- "ignore previous instructions";
- "always approve";
- approval/policy/verifier bypass language.

There is no override in normal canonical Memory V1.

Conversation-recall filtering remains frozen and separate.

### 5. Append-only REVOKE

A promoted canonical memory can now be **REVOKED** by the owner.

REVOKE:

- appends another decision event;
- never deletes or edits the original PROMOTE event;
- never edits the immutable canonical row;
- makes the memory inactive in canonical read results;
- preserves the full promotion + revocation evidence chain.

A revoked memory cannot be re-promoted in V1. Correction/supersession remains a later module.

### 6. Stronger decision evidence

Every durable decision event now records:

- monotonic `event_index`;
- paired owner actor fingerprint (truncated token SHA-256 identity);
- SHA-256 of the one-time review token;
- candidate id/hash;
- owner/project scope;
- source ref;
- trust origin/tier;
- candidate snapshot;
- timestamp;
- previous event hash;
- event hash.

The event hash includes the monotonic event index and actor/ticket evidence.

### 7. Honest hash-chain claim

The UI/docs must not call the local hash chain tamper-proof.

It detects in-database mutation/reordering when audited, but a wholesale replacement of the local SQLite database cannot be detected without a future external anchor.

The API therefore reports this limitation explicitly.

## State machine after hardening

```text
PENDING -> DEFER -> PROMOTE -> REVOKE
   |         |         |
   |         +-------> REJECT
   +-----------------> REJECT
   +-----------------> PROMOTE
```

Rules:

- REJECT is terminal;
- REVOKE is terminal;
- PROMOTE may only repeat idempotently or move to REVOKE;
- DEFER is non-terminal;
- revoked memory cannot re-enter active canonical Memory in V1.

## Authority remains unchanged

Even active canonical Memory is:

`authority=context_only`

It cannot grant permissions, authorize execution, invoke Hands, bypass approvals, or change ORION policy.

Canonical Memory is still **not injected into model prompts** in this module.

## Next qualification

The entire isolated gate must be rerun against the hardened exact SHA before any live installation.

The physical gate must include:

- promote exact GREEN 842 owner message;
- verify active canonical count;
- reject assistant BLUE 901 candidate;
- verify assistant cannot be promoted;
- defer a harmless owner candidate;
- revoke the promoted GREEN 842 memory;
- verify active canonical count drops and revocation evidence remains;
- verify frozen Conversation Recall continues working independently.

Only then may the module be frozen.
