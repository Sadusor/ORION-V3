# V3-RUN-049 — production routine read-only Hand execution staged

Date: 2026-10-04

## Purpose

Close the first complete safe ORION production loop from owner language to a
real PC read-only effect:

```
OWNER
 -> 9B governor
 -> semantic ORION PROPOSAL
 -> reload/revalidate canonical proposal
 -> ORION Action Lease
 -> pinned OpenJarvis filesystem-search Hand
 -> ORION EvidenceEnvelope
 -> deterministic ORION verifier
 -> RESULT
```

## Reuse, not rebuild

RUN-049 reuses the already physically proven donor path:
- OpenJarvis pin:
  `309a4f1044ccfb2032264832a31fef2f1d314586`
- `orion_filesystem_search`
- ORION `LeaseAuthority`
- ORION `AuthorityGateway`
- OpenJarvis default-deny capability policy
- `normalize_filesystem_search_evidence()`

No second file-search implementation is introduced.

## Production execution bridge

New:
`src/orion_v3/operator/execution.py`

Before a lease is issued, ORION reloads the proposal from the append-only Event
ledger and proves:
- exact task ownership;
- event type is PROPOSAL;
- event kind is `capability_action_proposed`;
- registered capability exists;
- capability version still matches registry;
- parameters are still canonical after deterministic normalization;
- action SHA256 recomputes exactly;
- approval class is READ_ONLY;
- production executor exists for the capability.

Only `fs.search_exact` is admitted in this first auto-dispatch slice.

Non-read-only proposals are denied.

## Single-entry dispatch

The same canonical proposal may enter routine execution only once.

A second dispatch attempt is denied as:
`proposal_already_dispatched`.

This prevents model/retry-loop duplication from silently firing the same Hand
twice.

## Physical owner request

Find:
- `pyproject.toml`
- `gateway.py`

inside:
- `active_project`

Forbidden:
- edit;
- reveal;
- browser/open;
- publish;
- cloud call.

Expected real evidence includes at least:
- `pyproject.toml`
- `src/orion_v3/authority/gateway.py`

The trusted absolute repo root must never appear in normalized/verified evidence.

## Canonical causal history

Required exact event sequence:
1. PROPOSAL
2. ACTION
3. EVIDENCE
4. RESULT

Parent chain must be exact:
`PROPOSAL -> ACTION -> EVIDENCE -> RESULT`

A RESULT is created only after deterministic evidence verification succeeds.

## Evidence verifier

The verifier requires:
- outcome = CONFIRMED;
- operation = `filesystem.search`;
- implementation =
  `openjarvis.tool.orion_filesystem_search.v1`;
- searched locations exactly match proposal;
- match_count is internally consistent;
- every match stays in an allowed location;
- every path is safe project-relative;
- every returned basename was explicitly requested.

## PASS meaning

PASS proves the first real production Hand execution controlled by the new V3
governor/control-plane architecture.

The 9B chooses semantics only. ORION owns:
- proposal truth;
- hash/version validation;
- lease issuance;
- trusted root;
- Hand dispatch;
- evidence normalization;
- deterministic verification;
- final RESULT truth.
