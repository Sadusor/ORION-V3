# V3-RUN-047 — live Groq cloud round-trip staged

Date: 2026-10-04

## Purpose

Connect one real hosted coding specialist to the already-proven ORION cloud
request/response contracts.

This is deliberately one provider and one exact model:
- provider: Groq
- requested model: `openai/gpt-oss-120b`
- credential: existing `GROQ_API_KEY`

No provider fallback or model substitution is allowed.

## Donor provenance

The bounded connector pattern is transplanted from proven old ORION:
- `orion_core/independent_peer_evidence.py`
- old ORION SC1 cloud self-coding gate

Reused principles:
- exact requested/served model identity;
- no tools;
- no Hands;
- no routing authority inside provider connector;
- retry only transient 429/503 against the same provider/model;
- no fallback substitution;
- response captured as advisory evidence.

V3 implementation:
- `src/orion_v3/operator/cloud_provider.py`

## Live flow

```
ORION queue cloud:coding
 -> freeze exact request
 -> build bounded advisory prompt
 -> Groq openai/gpt-oss-120b
 -> exact served-model check
 -> capture response hash/id
 -> RUN-046 ingestion contract
 -> immutable REVIEW
 -> orion:governor inbox
```

## Privacy / logging

The gate does not print the cloud answer text.

Remote evidence contains only:
- provider/model identity;
- provider latency;
- prompt hash;
- response hash;
- response character count;
- ORION request/event identities.

The live answer exists only in the temporary gate state and is deleted after the
gate. Durable answer retention will be a separate explicit product decision.

## Authority

The provider receives:
- no tool schemas;
- no filesystem access;
- no shell;
- no browser;
- no Hand;
- no approval authority;
- no task mutation authority.

The returned answer becomes only an ORION `REVIEW` event with
`authority=advisory_only`.

RUN-047 must create:
- 0 DECISION events;
- 0 ACTION events;
- 0 Hand executions;
- 0 fallback substitutions.

## Cost rule

Exactly one bounded provider inference is intended.
`max_tokens=700`.

No surprise second provider or automatic fallback is permitted.

## Failure semantics

Fail/blocked if:
- `GROQ_API_KEY` is missing;
- the provider request fails;
- Groq serves a model other than `openai/gpt-oss-120b`;
- provider message identity is missing;
- response is empty;
- request/response binding changes;
- the response creates authority-bearing state.

A provider availability/quota failure does not invalidate RUN-046; it means only
the live connector is not currently proven.

## PASS meaning

PASS proves a real cloud model can think for ORION and return advisory evidence
without becoming an execution or authority peer.
