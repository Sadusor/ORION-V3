# V3-RUN-040 — partial efficiency benchmark, IQ4 routing failure

Date: 2026-10-04

Status: **PHYSICAL FAIL WITH VALID PARTIAL METRICS**

Remote source SHA:
`669fbf710bebd9b7c19ab700b8841a865cb92d54`

Session:
`6ee6a91069b5`

Exact V3 SHA:
`2da371df93a4e9f68e6b007c8f50ba9e16dfcca0`

## Qwen3.6-35B-A3B

Correctness:
- PASS
- 4 actions

Measured:
- wall: 69.919 s
- peak GPU delta: 14490 MB
- peak RAM delta: 9391.9 MB
- Ollama processor split: 39% CPU / 61% GPU
- Ollama context: 4096

## Qwen3.8-27B

Correctness:
- PASS
- 4 actions in this run

Measured:
- wall: 149.919 s
- peak GPU delta: 13903 MB
- peak RAM delta: 7215.3 MB
- Ollama processor split: 29% CPU / 71% GPU
- Ollama context: 4096

## Qwen3.8-27B IQ4

Model:
`batiai/qwen3.8-27b:iq4`

Correctness:
- FAIL in EDIT_CASE

Observed action sequence:
- search_exact_files
- file_editor
- file_editor
- file_editor

The benchmark required the edit case to use only FileEditor.

Measured before failure:
- wall: 140.082 s
- peak GPU delta: 14015 MB
- peak RAM delta: 3339.4 MB
- Ollama processor split: 12% CPU / 88% GPU
- Ollama context: 16384

Interpretation:
IQ4 was materially lighter on system RAM and more GPU-resident, but it failed the
routing-efficiency/correctness gate in this run.

## Thinking status correction

The operator substrate already configured:
`reasoning_effort="none"`

Pinned OpenHands uses LiteLLM 1.93.0.

Pinned LiteLLM 1.93.0 maps Ollama-chat reasoning effort:
- none -> think=false
- low/medium/high -> think=true for non-gpt-oss Ollama models.

Therefore RUN-040's IQ4 candidate was already **thinking OFF**.

The failure must not be attributed to hidden thinking.

## Fairness defect discovered

IQ4 ran with a 16384-token runtime context while the larger models ran at 4096.

Context allocation affects memory and potentially latency, so RUN-040 is not a
clean final resource comparison across all models.

## Next controlled decision benchmark

Use one common runtime context:
`num_ctx=4096`

Compare:
1. qwen35-9b-orion:latest — thinking OFF
2. qwen3.6:35b-a3b — thinking OFF
3. qwen3.8:27b — thinking OFF
4. batiai/qwen3.8-27b:iq4 — thinking OFF
5. batiai/qwen3.8-27b:iq4 — thinking ON

For IQ4 ON use reasoning_effort=medium. Under pinned LiteLLM this maps to
Ollama think=true.

Correctness/authority remains a hard gate for every candidate.
