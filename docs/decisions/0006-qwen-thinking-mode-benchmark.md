# Decision 0006 — Qwen Thinking Mode Hard A/B Benchmark

Date: 2026-10-04  
Status: STAGED

## Question

Does Qwen 9B thinking mode produce materially better ORION intent interpretation on hard, policy-sensitive requests, enough to justify its latency/token cost?

The earlier trivial V2 prepare comparison was not sufficient because thinking OFF and ON produced the same simple three-field proposal.

## Benchmark

Run the same local model with temperature 0 on eight harder interpretation cases in both modes:

- thinking OFF
- thinking ON

The cases cover:

- conditional local-search -> web fallback;
- conditional local result blocking network use;
- ambiguous recipient requiring clarification;
- prompt injection embedded in file content;
- current explicit request overriding remembered defaults;
- path traversal escaping an approved root;
- install request that still requires confirmation;
- destructive action with exact scope.

The model has advisory authority only. The benchmark performs no Hand dispatch and no real file, network, install, send, or delete action.

## Scoring

Each mode is scored deterministically on the same eight structured fields per case, plus critical-case pass/fail gates.

Compare:

- total field accuracy;
- critical cases passed;
- median latency;
- total output tokens.

Quality wins before speed. If thinking ON improves critical correctness or total structured accuracy, that is evidence to keep it enabled for hard interpretation. If quality ties, latency/token cost becomes the deciding factor.

No production default is changed by the benchmark itself.
