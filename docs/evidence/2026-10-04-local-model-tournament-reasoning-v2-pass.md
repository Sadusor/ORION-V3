# Local Model Tournament — Reasoning V2 Physical PASS

Date: 2026-10-04  
Status: PASS  
Source repo: `Sadusor/Orion`  
Source SHA: `438791c52b19d03e037a629f5abb092395593f13`  
Session: `2e43a124646f`  
Completed models: 7

## Leaderboard

| Rank | Model | Mode | Critical | Full | Median latency | Output tokens |
|---:|---|---|---:|---:|---:|---:|
| 1 | qwen35-9b-orion | THINKING | 25/36 | 9/36 | 15.380 s | 21,147 |
| 2 | gemma4-12b | THINKING | 24/36 | 11/36 | 9.638 s | 25,763 |
| 3 | qwen35-9b-orion | FAST | 23/36 | 8/36 | 3.192 s | 3,379 |
| 4 | gemma4-12b | FAST | 21/36 | 6/36 | 1.742 s | 3,741 |
| 5 | gemma2-9b | NORMAL | 16/36 | 7/36 | 5.309 s | 3,546 |
| 6 | ministral3-8b | NORMAL | 15/36 | 6/36 | 1.292 s | 3,321 |
| 7 | llama31-8b | NORMAL | 12/36 | 3/36 | 1.031 s | 3,057 |
| 8 | phi4-mini | NORMAL | 6/36 | 6/36 | 0.744 s | 3,093 |
| 9 | granite4-tiny-h | NORMAL | 3/36 | 0/36 | 0.643 s | 2,986 |

## Winners

- FAST / normal-mode winner: `qwen35-9b-orion`
- THINKING winner: `qwen35-9b-orion`

Gemma 4 12B was the closest challenger:
- THINKING had one fewer critical pass than Qwen thinking, but two more full passes and lower median latency;
- FAST was faster than Qwen FAST but had two fewer critical passes.

## Interpretation

For the current ORION Reasoning V2 interpretation benchmark, the existing Qwen 3.5 9B ORION remains the strongest overall local candidate.

This supports keeping Qwen as the leading Personal Assistant / general interpretation model for the next gates.

It does **not** yet prove that Qwen is the best:
- project/coding coordinator;
- vision model on the exact installed runtime;
- concurrent two-lane configuration;
- personalized/fine-tuned model.

Those require separate benchmarks already added to the roadmap.

The tournament does not justify loading two different local models merely for role separation. The next concurrency test should first compare:
1. one Qwen model with two isolated logical contexts;
2. Qwen plus the strongest specialist challenger where the role-specific benchmark justifies it.

## Important quality note

No model passed all critical cases. This reinforces the architecture:
- language models remain advisory/interpreting components;
- deterministic ORION policy owns scope, approval, provenance and authority;
- unsafe/unreliable classes escalate rather than relying on model judgment alone.

## Evidence Pack

- state: `ready`
- observer-only: `true`
- authority effect: `none`
- SHA-256: `d975f7132d0daf43058d51ebbccc1dfe76d77da0ea03f5797e7048095ee1d0a1`
- size: 715473 bytes
- steps: 40
- PNG: 41
- SVG: 41
