# V3-RUN-013 — Canonicalization Isolation FAIL

Date: 2026-10-03

Status: **FAIL — structured-output boundary not exercised**

## Identity

Remote task SHA:
`8d04ba79ac52d9a6a85d7ee14655f49902a3bc53`

Remote attempt:
`414`

Exact V3 SHA:
`aee9b992d381c44abef965afda86a800d7db3b44`

## Result

The benchmark completed all 32 model calls, but the semantic/canonicalization
pipeline did not receive any parsed model object.

Observed aggregate markers:
- strict JSON rate: **0.0000**
- contract valid rate: **0.0000**
- one turn / zero tools: **1.0000**
- total tokens: **12,318**
- average tokens/request: **384.9**
- average latency: **1117.7 ms**

All 32 parsing failures were:
`json.loads -> Expecting value: line 1 column 1`.

## Root cause

The raw Qwen responses were JSON objects wrapped in Markdown code fences.

Example shape:

```text
```json
{ ... }
```
```

The benchmark used OpenJarvis `SimpleAgent`.

Source audit after the failure found:
- pinned OpenJarvis `OllamaEngine.generate()` supports
  `response_format` and maps it to Ollama JSON mode;
- `SimpleAgent.run()` calls `_generate(messages)` without exposing
  `response_format`;
- therefore V3-RUN-013 was still relying on prose instructions to make the model
  produce machine JSON.

This means the run did **not** falsify the canonicalizer architecture.
It falsified the inference-boundary assumption.

## Useful raw observations

Although they were not parsed, the escaped raw output shows that several model
responses contained plausible semantic objects. It also exposed remaining
surface variants such as:
- optional ambiguity fields returned as null;
- intent labels occasionally decorated with a signature;
- a scalar entity occasionally returned as a singleton list.

Those remain candidates for deterministic canonicalization after native JSON
syntax is physically proven.

## Decision

Do not strip Markdown fences with an ad-hoc parser and call that structured
output.

Use the donor's native Ollama JSON mode.

V3-RUN-014 keeps:
- the same frozen 32-case corpus;
- the same Qwen3.5-9B model;
- the same prompt;
- the same canonicalizer/resolver;
- the same pass thresholds.

The only intentional change is:
OpenJarvis one-turn generation uses `ResponseFormat(type="json_object")`.

This isolates the structured-output boundary.
