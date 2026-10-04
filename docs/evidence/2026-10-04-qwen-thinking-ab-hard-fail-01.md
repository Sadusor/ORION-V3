# Qwen Thinking ON vs OFF — Original Hard Probe FAIL

Date: 2026-10-04  
Status: FAIL — HARNESS SERIALIZATION DEFECT, WITH USEFUL PRELIMINARY SYSTEMS DATA  
Source SHA: `76770cda200d22c52aab6fb351ef6d2823ef49d9`  
Session: `418e25e2a0d2`

## Why the run was marked FAIL

The eight-case comparison itself completed, but the harness crashed while saving the final JSON evidence because the original case definitions contained Python `set` values.

Observed terminal exception:

`TypeError: Object of type set is not JSON serializable`

Therefore this run must not be treated as the final thinking-mode benchmark.

## Preliminary data worth preserving

The old benchmark labels were later rejected by DeepSeek as too leading, so its quality winner is not authoritative.

However, the runtime behavior is still useful systems evidence:

- thinking OFF median latency: `1.209 s`
- thinking ON median latency: `42.365 s`
- thinking ON/OFF latency multiplier: `35.04x`
- thinking OFF total output tokens: `574`
- thinking ON total output tokens: `45,055`
- two thinking-ON calls ran to roughly `16,000` generated tokens and produced no parseable final JSON;
- those two calls took roughly `230 s` and `252 s`.

This demonstrates that unrestricted thinking can become far more than "slightly slower" on harder prompts, independent of whether the old expected labels were good.

## Evidence Pack

The outer observer Evidence Pack still completed successfully:

- state: `ready`
- observer-only: `true`
- authority effect: `none`
- SHA-256: `8c9d1b8638084694db19f1d56690ec4bb9711243049be38953195bf44ad7b79f`
- steps: 30
- PNG cards: 31
- SVG cards: 31

## Consequence for replacement benchmark

Before running the DeepSeek-informed Reasoning V2 benchmark:

- cap generated tokens identically for ON and OFF;
- apply a request-time budget;
- treat a per-call timeout/error as a scored failure instead of crashing the whole benchmark;
- keep the model loaded and preserve the three-repeat/order-control design;
- do not reuse the original benchmark's quality verdict.

Reasoning V2 now uses a `1024` generated-token cap and `60 s` request timeout per call.
