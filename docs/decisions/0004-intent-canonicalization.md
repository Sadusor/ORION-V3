# Decision 0004 — Literal Semantics, Deterministic Canonicalization

Date: 2026-10-03

Status: **ACCEPTED FOR PHYSICAL QUALIFICATION**

## Decision

Qwen is a semantic interpreter, not a canonical data normalizer.

The lightweight ORION path is now:

```text
user
 -> Qwen literal semantic Intent/entities
 -> ORION deterministic canonicalizer
 -> ORION deterministic Intent resolver
 -> ORION policy/authority
 -> vetted Hand
 -> evidence/verifier
```

## Qwen owns

- semantic intent;
- literal entity extraction;
- genuine semantic ambiguity;
- composition/multiple-action detection.

Qwen does not own:
- capability selection;
- canonical aliases;
- optional null/omit conventions;
- policy/approval questions;
- trusted path resolution;
- authority.

## Canonicalizer owns

- null optional field removal;
- aliases and canonical vocabulary;
- quantifier normalization such as every -> all;
- app/browser aliases;
- logical scope aliases;
- schema regularization;
- separation/logging of policy-style ambiguity text;
- preservation of exact payload content where byte/text identity matters.

## Resolver owns

- canonical Intent + entities -> capability;
- NO_CAPABILITY;
- AMBIGUOUS;
- later deterministic shortlist/escalation policy.

## Policy owns

- effect class;
- approval;
- trusted scope;
- authorization;
- dispatch.

## Benchmark rule

Benchmarks score canonicalized semantic output, not arbitrary model surface form.

Examples:
- omitted optional field and null optional field are equivalent after canonicalization;
- every/all are equivalent after canonicalization;
- genuinely ambiguous phrases must be labeled ambiguous rather than forced into one golden intent.

Policy/approval text in Qwen's ambiguity output remains a contract-quality failure even if the canonicalizer filters it before resolution.

## Evidence

This decision follows:
- V3-RUN-011 direct capability-router failure;
- V3-RUN-012 incomplete intent benchmark;
- external review identifying over-specified surface-form labels.

V3-RUN-013 will physically test canonicalization isolation.
