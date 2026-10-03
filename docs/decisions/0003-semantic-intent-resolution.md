# Decision 0003 — Separate Semantic Intent from Capability Selection

Date: 2026-10-03

Status: **ACCEPTED FOR PHYSICAL QUALIFICATION**

## Evidence that triggered this decision

V3-RUN-011 physically tested Qwen3.5-9B as a direct one-shot capability
selector over a five-capability catalog.

Observed:
- supported intent accuracy: 12/15 = 80%;
- exact params: 12/15 = 80%;
- unsupported safe rejection: 7/7 = 100%;
- strict JSON: 100%;
- contract-valid: 100%;
- one turn / zero tools: 100%;
- average total tokens/request: 725.1;
- average latency/request: ~961.8 ms.

The three misses were all semantically adjacent capability choices:
exact-name search vs listing, plain search vs reveal behavior, and
non-recursive search.

V3-RUN-011-R2 did not reach Qwen. It failed in a Python dynamic-import wrapper
and is harness evidence only.

## Decision

Qwen does **not** select ORION capabilities.

Qwen produces a stable semantic Intent object.

ORION deterministically maps Intent + entities to:
- an exact capability and typed params;
- NO_CAPABILITY;
- AMBIGUOUS / clarification;
- later, a known workflow/escalation class.

Target:

```text
user sentence
  -> optional tiny deterministic fast-path
  -> Qwen semantic Intent + entities
  -> deterministic Intent Resolver
  -> semantic Capability Registry
  -> authority/policy
  -> vetted Hand
  -> evidence/verifier
```

## Why

The Intent taxonomy should change much more slowly than concrete capabilities.

Adding/replacing an implementation or adding another capability for an existing
intent must not enlarge Qwen's prompt.

Qwen is good at:
- language understanding;
- entity extraction;
- context/referent interpretation;
- detecting multiple requested actions;
- expressing ambiguity.

ORION is better suited to:
- capability selection;
- specificity/priority rules;
- availability;
- trusted bindings;
- effect/approval classes;
- authority;
- deterministic fallback/escalation.

## Important safety correction

The model should not be responsible for deciding that a recognized request is
"safe" or "unsafe".

Example:

`Close Chrome`

Qwen may produce:
`CLOSE_APP { app: chrome }`

If no `app.close` capability is registered, the deterministic resolver returns
`NO_CAPABILITY`.

No execution occurs.

Similarly a destructive semantic request can be understood correctly while
policy still denies or requires stronger authorization later.

Semantic understanding is not authorization.

## Intent object v0

Model-facing fields:

```json
{
  "intent": "LOCATE_NAMED_FILES",
  "entities": {
    "names": ["README.md"],
    "scope": "active_project",
    "recursive": true,
    "reveal_containing_folders": false
  },
  "ambiguities": [],
  "composition": false
}
```

No capability IDs.

No implementation.

No approval/effect class.

No trusted host path.

No credentials.

No model-supplied confidence is authoritative.

## Resolver confidence

Do not trust model self-reported confidence for authority.

Resolver certainty is derived from deterministic match quality:
- exact rule match;
- later lexical shortlist;
- later embedding shortlist if evidence justifies it.

If deterministic resolution remains ambiguous, ask the user.

## Fast path

A future deterministic fast path may bypass Qwen for a **small** set of
extremely common unambiguous patterns.

It must not become a general regex language parser.

The first Intent experiment does not require the fast path; it isolates the
Intent abstraction itself.

## Retrieval/scaling direction

At larger scale:
1. rules first;
2. lexical/FTS shortlist second;
3. embeddings only if evidence shows rules + lexical are insufficient.

Never feed the full capability catalog to Qwen as the normal architecture.

## Qwen long-term role

Qwen3.5-9B is primarily:
- semantic interpreter;
- workflow coordinator;
- memory/context foreman;
- bounded escalation/context decision helper.

It is not:
- authority;
- security policy;
- capability implementation selector;
- PASS/FAIL verifier.

## Next physical experiment

V3-RUN-012:

- Intent taxonomy: small and capability-independent;
- Qwen outputs Intent objects only;
- rules-only deterministic resolver;
- same 22 requests from V3-RUN-011;
- plus 10 new adversarial/paraphrase cases;
- no capability catalog in Qwen prompt;
- no tools;
- one inference turn;
- measure intent accuracy, entity accuracy, resolver dispatch correctness,
  no-capability/ambiguity safety, JSON/contract validity, tokens and latency.

Target gate:
- resolver safe no-dispatch on unsupported/ambiguous/destructive cases: 100%;
- strict JSON: 100%;
- Intent contract valid: 100%;
- one turn / zero tools: 100%;
- semantic intent accuracy: >=95%;
- exact entities: >=90%;
- resolver correctness: 100% for cases where deterministic rules are defined;
- average total tokens/request: <400;
- average latency target: <1 second.

Do not lower safety thresholds to obtain a PASS.
