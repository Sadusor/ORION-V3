# Decision 0010 — Multi-Lane Local Assistants and Personal Learning

Date: 2026-10-04  
Status: OWNER-APPROVED DIRECTION  
Execution authorization: NONE IMPLIED

## Owner intent

ORION must remain useful as a personal assistant while a long-running project workflow is active.

Example: while an app project is being planned, coded, reviewed or tested, the owner must still be able to ask ORION to open an app, find a file, search locally, inspect a download, summarize something, or perform other normal PC-assistant work without losing or corrupting project state.

The owner also wants at least one local model to become genuinely personalized to their files and working history, including intentionally supplied/downloaded data and visual material.

## Decision

ORION will support multiple **logical assistant lanes** under one authority plane.

The first two logical roles are:

### 1. Personal / Desktop Assistant

Purpose:

- low-latency everyday PC control;
- local file search/open/reveal;
- browser/navigation requests;
- summaries and lightweight reasoning;
- vision/perception where the selected model/runtime physically supports it;
- access to ORION-owned personal/project memory by retrieval.

Target behavior:

- always available even while a project workflow is active;
- prefer FAST/non-thinking mode for simple unambiguous requests;
- escalate to bounded thinking only when the request class earns the latency;
- use deterministic Hands for execution.

### 2. Project / Coding Coordinator

Purpose:

- maintain the active project's context;
- understand project goals and roadmap;
- summarize or critique cloud-coder/reviewer output;
- translate approved project work into ORION contracts;
- track tests, evidence, pending approvals and handoffs;
- act as an offline/local fallback when cloud coding help is unavailable.

This local role is not automatically the primary code generator. The established low-consumption workflow remains:

`cloud coder/reviewer -> ORION authority -> deterministic coding Hands`

unless later evidence shows a local coding model is competitive enough to take more of that role.

## One model or two models

"Two assistants" does not require two independent copies of model weights.

ORION may implement the two logical assistants in either form:

1. **one selected model, separate contexts/sessions** for Personal and Project roles; or
2. **two different local models** when benchmark evidence shows that specialization is worthwhile.

If the same model wins both roles, ORION should prefer one resident weight set with isolated conversations/context/state rather than loading duplicate copies merely to create two identities.

If different models win the roles, ORION may keep both resident when measured VRAM/RAM/latency permits it.

No assumption will be made that small models are a GPU bottleneck on the owner's hardware. Concurrency will be measured physically rather than designed around an unproven limitation.

## Scheduler

ORION, not the models, owns job routing.

The scheduler may use deterministic metadata such as:

- lane: personal / project / benchmark / reviewer;
- task class: read, UI navigation, bounded write, destructive, coding;
- model capability: vision, structured output, code, reasoning;
- thinking mode required by the adaptive policy;
- current model residency;
- context size;
- CPU/GPU/VRAM/RAM observations;
- task priority;
- owner STOP/pause requests.

Models never gain authority because they are assigned a lane.

## Concurrency requirements

A project task must not monopolize the personal assistant.

The target behavior is:

- project work may continue, wait for cloud output, run tests or wait for owner approval;
- the Personal Assistant remains responsive;
- each project retains isolated state and provenance;
- each lane has its own status and stop/pause semantics;
- one global STOP must still be capable of terminating the intended active execution safely;
- task outputs cannot silently cross project boundaries.

After the current small-model tournament, ORION should run a dedicated concurrency benchmark rather than guessing:

- one Personal Assistant request stream;
- one Project/Coding Coordinator stream;
- same-model dual-context variant;
- two-model variant where relevant;
- measure response latency, throughput, CPU, GPU, VRAM/RAM and interference.

## Personal learning: two separate layers

The phrase "train it on my files" is split into two different mechanisms.

### Layer A — ORION knowledge/memory retrieval (first priority)

Personal files should become usable immediately without retraining model weights.

Approved sources may include:

- project repositories and documents;
- files intentionally downloaded from ChatGPT or other assistants;
- files intentionally downloaded from Chrome;
- exported browser/bookmark/history data when the owner explicitly supplies it;
- PDFs, images, screenshots and scans;
- owner notes;
- accepted ORION task histories and evidence;
- selected conversation exports.

ORION ingests these into its own replaceable memory/index with:

- source path or source identity;
- project/person scope;
- timestamp;
- content hash;
- provenance/trust class;
- text extraction where applicable;
- image/vision representation where applicable;
- supersession/version relationship;
- explicit deletion/forgetting handling.

At query time ORION retrieves only relevant evidence and supplies it to the selected model.

This is the default meaning of "learn my files" because it is:

- immediately updateable;
- provenance-backed;
- reversible;
- rebuildable;
- model-independent;
- less likely to cause catastrophic forgetting;
- compatible with model replacement.

Raw files do not become authority.

### Layer B — optional model adaptation / fine-tuning

A local model may later be adapted with LoRA/QLoRA or another replaceable adapter, but only from a curated training set.

Do **not** continuously fine-tune on every raw file.

Candidate training examples should come from high-quality owner-approved material such as:

- corrected ORION interpretations;
- accepted task plans;
- preferred terminology;
- repeated personal workflow patterns;
- project conventions;
- successful structured-output examples;
- selected visual examples and labels where the chosen multimodal training stack supports them.

The base model remains immutable. Personalization should preferably live in a detachable adapter plus ORION memory.

Every adapter must have:

- dataset manifest and hashes;
- source provenance;
- explicit exclusion of secrets/credentials unless separately authorized;
- train/eval split;
- pre/post benchmark;
- rollback path;
- versioned artifact;
- no authority privileges.

A personalized model that performs worse on ORION safety/interpretation gates must not be promoted.

## Vision

Vision is strategically important because many useful personal sources are visual:

- screenshots from the PC/browser;
- PDF pages;
- scanned documents;
- photos;
- UI state;
- charts/diagrams.

A model should not be selected as the long-term Personal Assistant solely from text benchmarks if another candidate offers materially better vision while remaining fast enough.

The currently used `qwen35-9b-orion` family is a leading personalization candidate, but its exact installed runtime/package must pass a physical vision-capability benchmark before ORION treats vision as proven.

The vision test should check:

- image input accepted by the exact local runtime;
- screenshot understanding;
- text/diagram extraction without OCR-only dependency;
- grounding to the supplied image rather than hallucinated context;
- provenance linking from extracted facts back to the original file/image;
- latency and VRAM impact.

## Data ingestion boundary

ORION must not silently scrape or train on everything visible on the PC.

Personal learning is owner-controlled.

Default source rule:

`explicitly selected source / approved folder / approved project -> ingest`

not:

`entire computer -> train automatically`

Browser and assistant data can be added by:

- owner-downloaded files;
- explicit exports;
- a future Browser Hand saving approved pages/screenshots;
- explicit connector/import flows.

Credentials, cookies, tokens and unrelated private data remain excluded by default.

## Model-selection gates

The current general-model tournament is not enough to permanently assign both roles.

After it completes:

1. choose the strongest FAST general candidates;
2. preserve the adaptive thinking evidence;
3. run a small coding/project-coordinator benchmark;
4. run a vision + personal-file retrieval benchmark;
5. run same-model vs two-model concurrency;
6. choose role assignments from measured quality, latency and resource cost.

Possible outcomes include:

- Qwen for both roles with two logical contexts;
- Qwen Personal + another model Project;
- another model Personal + Qwen Project;
- one fast model for both roles plus cloud specialists for difficult work.

The architecture must support all four without redesigning ORION.

## UI consequence

The new V3 UI must represent work as lanes/projects rather than one global "busy" state.

Minimum visible concepts:

- Personal Assistant: READY / THINKING / ACTING;
- active project(s): RUNNING / WAITING / APPROVAL / PAUSED;
- active model + mode per lane;
- lightweight resource state where useful;
- per-task pause/stop;
- one truthful global STOP.

The owner should be able to ask the Personal Assistant for normal PC work even while an app project is active.

## Non-decision

This document does not select the final local model, start fine-tuning, ingest personal files, enable background scraping, or authorize any training job.

Those steps require separate bounded tests and explicit owner approval.
