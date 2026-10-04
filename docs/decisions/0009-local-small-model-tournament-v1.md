# Decision 0009 — Local Small-Model Tournament V1

Date: 2026-10-04  
Status: STAGED

## Goal

Compare small local models on ORION's own 12-case Reasoning V2 interpretation benchmark rather than relying on generic academic leaderboards.

One Remote task performs the approved network downloads and then runs the benchmark.

## Candidates

Baseline:

- `qwen35-9b-orion:latest` — owner's existing ORION-tuned Qwen 3.5 9B; never replaced or auto-downloaded.

Official Ollama-library challengers:

- `gemma2:9b`
- `gemma4:12b`
- `llama3.1:8b`
- `ministral-3:8b`
- `phi4-mini:3.8b`
- `granite4:7b-a1b-h`

Phi-4 Mini and Granite 4 Tiny-H are additional low-consumption challengers added because ORION values latency and efficiency, not parameter count alone.

## NVIDIA Nemotron Nano 9B V2

The requested NVIDIA Nemotron Nano 9B V2 is intentionally not auto-downloaded in this one-click task.

Reason: the NVIDIA 9B-v2 weights are official, but the readily available Ollama-compatible GGUF quantizations found for the 9B-v2 model are community conversions rather than an official NVIDIA/Ollama-library package. ORION will not silently trust a community conversion simply to fill a benchmark slot.

It can be added later after the owner explicitly approves a chosen quant/source, or through a separately qualified official runtime path.

## Download behavior

The task:

1. starts/uses local Ollama;
2. checks which candidates are already installed;
3. computes expected missing download size;
4. checks model-storage free disk space with a 6 GB safety margin;
5. fails before downloading if free space is insufficient;
6. pulls missing official candidates sequentially through Ollama;
7. records per-model download failures and continues with other candidates;
8. leaves downloaded models installed after the tournament so the owner can decide what to keep.

Expected maximum new download volume if none of the challengers are installed is approximately 31 GB before Ollama metadata/overhead.

## Benchmark

Every candidate runs the same twelve Reasoning V2 interpretation cases with:

- identical ORION policy text;
- identical output schema and deterministic labels;
- temperature 0;
- 1024 generated-token ceiling;
- 60-second per-call timeout;
- three scored repetitions;
- one discarded warmup per tested mode;
- deterministic order changes across repetitions;
- no Hand dispatch and no real file/web/install/send/delete action.

Models without a reasoning mode run their normal mode.

Known thinking-capable tournament candidates run both:

- FAST / thinking OFF
- THINKING / thinking ON

For V1 those are the existing Qwen 9B and Gemma 4 12B.

## Ranking

Rank model-mode entries by:

1. critical-policy passes / 36;
2. full passes / 36;
3. median latency;
4. output-token cost.

Quality therefore beats speed, while latency and token cost resolve quality ties.

The task emits separate FAST and THINKING winners.

## Safety

The only intended real side effect is downloading explicitly approved model artifacts from the official Ollama library.

The benchmark itself has:

- authority effect: none;
- Hand dispatch: none;
- no real task side effects.

No production ORION model/default is changed by the tournament.
