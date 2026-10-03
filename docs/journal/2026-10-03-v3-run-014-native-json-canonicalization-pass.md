# V3-RUN-014 — Native JSON + Canonicalization Physical PASS

Date: 2026-10-03

Status: **OWNER-OBSERVED PHYSICAL PASS**

## Identity

Exact ORION-V3 checkout used by the bootstrap:

`80f17408b105f789113d6ac9717cb6d24d9de465`

Bootstrap:

`scripts/v32_structured_canonicalization_bootstrap.ps1`

Benchmark:

`scripts/v32_qwen_structured_canonicalization_benchmark.py`

Model:

`qwen3.5:9b`

Pinned OpenJarvis donor:

`309a4f1044ccfb2032264832a31fef2f1d314586`

## Evidence source

This run was executed through the Manual / External AI Workbench lane using the
local V3 bootstrap.

The owner reported the run as PASS.

The legacy GitHub results branch was not updated with a fresh lane-result for
this manual run, so exact per-case aggregate values are not claimed here.

The bootstrap exits 0 only when:
1. the V3 regression suite passes; and
2. the benchmark's complete pass gate evaluates true.

Therefore the following threshold claims are justified by the observed PASS,
while exact values above/below each threshold remain unknown unless separately
captured from local evidence.

## Gates proven by exit-0 PASS

- hard no-dispatch rate: **100%**
- strict JSON rate: **100%**
- semantic contract-valid rate: **100%**
- one turn / zero tools: **100%**
- policy-clean rate: **100%**
- canonical semantic-intent accuracy: **>=95%**
- canonical entity accuracy: **>=90%**
- ambiguity detection: **>=85%**
- false ambiguity rate: **<=10%**
- deterministic resolver correctness for labeled cases: **100%**
- average total tokens/request: **<400**
- average latency/request: **<1000 ms**

## What changed from V3-RUN-013

V3-RUN-013 failed before semantic scoring because Qwen returned fenced JSON and
the benchmark used plain `json.loads()`.

Source inspection showed that pinned OpenJarvis already supports Ollama native
JSON mode through `response_format`, but `SimpleAgent.run()` does not expose
that argument.

V3-RUN-014 reused the same 32-case corpus and the same Qwen model while routing
the one-turn inference through OpenJarvis/Ollama native JSON mode.

No tool execution was added.

## Architectural conclusion

The currently supported lightweight-governor path is:

```text
user language
 -> Qwen3.5-9B literal semantic interpretation
 -> ORION deterministic canonicalization
 -> ORION deterministic intent resolver
 -> Capability / NO_CAPABILITY / AMBIGUOUS
 -> ORION policy/authority
 -> vetted Hand
```

This is stronger than the earlier direct-capability architecture because:
- Qwen does not need to know which capabilities currently exist;
- capability growth does not require feeding the full registry to Qwen;
- surface normalization belongs to deterministic ORION;
- unimplemented/destructive intents can be understood without being dispatched;
- the model remains one-turn/no-tools;
- authority remains outside the model.

## Scope of proof

This is a 32-case architecture qualification, not a production-scale language
benchmark.

Do not claim:
- arbitrary-language reliability;
- 100+ capability scalability;
- production readiness;
- robustness across all paraphrases/projects;
- that Qwen can authorize or execute actions.

A larger held-out benchmark is still required before calling the governor
production reliable.

## Next architectural priority

Stop spending time on prompt-format mechanics.

Return to the frozen roadmap:

1. expand/harvest semantic capabilities from proven legacy ORION mechanics;
2. implement canonical Memory + append-only local event exchange;
3. use Qwen as semantic interpreter/context foreman;
4. automate the cloud-AI Coding Factory around existing Coding Hands;
5. add Whole-PC escalation later.

The immediate next engineering slice should favor canonical Memory/local event
state because continuity is the highest remaining architectural risk.
