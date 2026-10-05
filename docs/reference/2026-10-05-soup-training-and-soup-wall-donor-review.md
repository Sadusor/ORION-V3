# Soup + Soup Wall donor review — 2026-10-05

Evidence label: **DOCUMENTED / NOT TESTED**

This note records a research candidate only. Neither project is adopted into ORION V3 by this document.

## Executive verdict

Two upstream projects from Alpamys Makazhan are relevant to ORION V3 for different reasons:

- **Soup** is a high-priority candidate for the optional personalized-model-adapter lane. It may reduce the engineering and VRAM cost of LoRA/QLoRA experiments and can export models/adapters back into local deployment workflows.
- **Soup Wall** is a high-priority security/control donor. Its deterministic, local, shadow-first action firewall overlaps strongly with ORION's own authority model, especially exact action gating, taint/egress controls, approval grants, audit/replay and regression gates.

The ORION rule remains unchanged:

> OWNER > ORION AUTHORITY > SUBSTRATE / DONORS > HANDS

Neither Soup nor Soup Wall may become an authority peer.

## Upstream references

- Soup: https://github.com/MakazhanAlpamys/Soup
- Soup Wall: https://github.com/MakazhanAlpamys/soup-wall

Both repositories report Apache-2.0 licensing at the time of this review.

Before any physical ORION qualification, pin the exact upstream revision and re-check license/provenance.

---

## 1. Soup — training / post-training donor

### What it is

Soup provides a YAML-driven local fine-tuning/post-training workflow. The advertised basic path is approximately:

```text
dataset + config
      ↓
    Soup
      ↓
 LoRA/QLoRA training
      ↓
 adapter / merged model
      ↓
 local evaluation
      ↓
 GGUF / local runtime path
```

The useful ORION idea is not "put ORION memory into model weights." The useful idea is to train a detachable specialist adapter on repeated ORION behavior after enough reviewed evidence exists.

### Layer-streaming claim

Soup's layer-streaming mode keeps the frozen base model out of GPU VRAM and streams decoder layers through the GPU while training the adapter.

Upstream publishes a benchmark for:

- Llama-3.1-8B-Instruct;
- NF4 + LoRA;
- RTX 3050 Laptop GPU with 4 GB VRAM;
- batch 1, sequence length 512;
- reported peak VRAM: **3.32 GB**;
- reported training throughput: **119.6 tokens/s**.

Important qualification: upstream states this measurement was made on v0.72.2, before a later correctness repair, and the 4 GB-card benchmark had not yet been re-run on the repaired version at the time of this review. Layer streaming is therefore a promising **BETA** capability, not an ORION-proven fact.

The 119.6 tokens/s figure is training throughput, not inference speed.

### Why it matters to ORION

ORION already creates potential training data as a side effect of governed operation:

- owner request -> interpreted intent;
- intent -> selected Hand/tool;
- safe action -> execute;
- risky action -> approval;
- scope violation -> deny;
- STOP -> priority override;
- hard reasoning -> route to stronger/cloud model;
- ambiguous factual state -> retrieve canonical memory;
- failed execution -> evidence-backed failure rather than invented success;
- corrected plan/tool sequence after a reviewed failure.

This suggests a future curated dataset made from **reviewed behavior traces**, not a dump of the memory database.

### Critical architecture boundary

Keep these two concepts separate:

- **ORION Memory = what ORION knows.**
- **Personalized adapter = how a replaceable model interprets/routs recurring ORION tasks.**

Canonical memory, provenance, roadmap, current project state and user facts stay in ORION-owned storage/retrieval. Do not bake them into weights as the primary memory mechanism.

### Proposed future benchmark

When V3.9A is reached, compare at minimum:

1. base small model with retrieval only;
2. same base + curated LoRA/QLoRA adapter;
3. current Qwen 3.5 9B governor baseline.

Candidate small-model sizes may include roughly 1B-4B-class models where supported, but model choice remains benchmark-driven.

Measure:

- intent classification accuracy;
- correct Hand/tool selection;
- unsafe action false-negative rate;
- unnecessary approval rate;
- scope/STOP compliance;
- hallucinated-success rate;
- latency;
- CPU/GPU/VRAM/RAM;
- power/energy where practical;
- adapter size and load time;
- regression against unseen held-out ORION traces.

### Dataset rules

Initial dataset should be deliberately small and clean rather than large and noisy.

Recommended first gate:

- approximately 200-500 owner/reviewer-approved examples;
- synthetic or scrubbed fixtures only in this public repository;
- no secrets;
- no raw private logs;
- provenance for every training example;
- explicit train/validation/held-out split;
- include negative and denial examples, not only successful actions;
- preserve failed attempts and corrected outcomes as separate provenance-backed records;
- version the manifest and adapter independently from the immutable base model.

Promotion requires pre/post ORION regression gates. A better training loss is not sufficient evidence.

### ORION disposition

**HIGH-PRIORITY TRAINING DONOR / BENCHMARK LATER**

Do not interrupt the current connector + product-UI build sequence for this work. V3.9A remains the correct lane.

---

## 2. Soup Wall — agent/security donor

### What it is

Soup Wall describes itself as a local firewall for AI-agent behavior. It covers:

- tool calls;
- tool results;
- MCP handshakes;
- subagent spawning;
- prompt-injection / secret / PII signals;
- taint tracking;
- action classes;
- egress-host controls;
- subagent authority checks;
- MCP manifest signals/pinning;
- first-match YAML policy;
- local audit logs;
- replay;
- preflight;
- human approval grants;
- guarded execution;
- a regression corpus / policy-change gate.

Its implementation is primarily Rust and upstream reports Apache-2.0 licensing.

### Strong overlap with ORION

The important alignment is philosophical:

- classifiers may provide signals;
- policy decides whether an action is allowed;
- enforcement can be deterministic and local;
- approvals can be bound to a specific action;
- subagents cannot silently gain authority;
- policy changes should be replayed against reviewed benign/attack traces;
- security can begin in shadow mode before enforcement.

This is close to ORION's existing design, but ORION remains the authority plane.

### Useful donor ideas to inspect

1. **Shadow-first enforcement**
   - Run policy in observe-only mode first.
   - Collect real verdict/evidence traces.
   - Promote to enforcement only after reviewed evidence.

2. **Replay gate for policy changes**
   - Every policy edit should be replayed against known-safe and known-hostile traces.
   - A policy edit must not silently weaken previously proven protections.

3. **Taint + egress reasoning**
   - Track whether untrusted content influences a later side effect.
   - Treat outbound network destinations as explicit policy inputs.

4. **Subagent authority monotonicity**
   - Child/subagent authority must be equal to or narrower than the parent.
   - No tool/permission expansion via delegation.

5. **MCP/tool-manifest pinning**
   - Detect or reject unexpected tool-definition changes before granting execution authority.

6. **Human approval grant shape**
   - Study binding approvals to exact action details, expiry and one-shot semantics.
   - Compare directly with ORION/OpenMuse frozen-plan-hash and Action Lease mechanics.

7. **Local audit + preflight**
   - Fail closed when the security reference monitor expected by the contract is absent.
   - Keep evidence locally inspectable.

### What ORION must reject

Do not import Soup Wall as a new top-level authority.

Reject any design where:

- a Soup Wall verdict can create ORION permission;
- a classifier can authorize an action;
- external YAML policy bypasses ORION's canonical PermissionGrant / Action Lease truth;
- a donor daemon owns STOP semantics;
- donor logs replace ORION canonical Task/Event evidence;
- a donor approval mechanism bypasses exact ORION approval binding.

The safe relationship is:

```text
owner request
    ↓
ORION authority
    ↓
proposal / model / agent
    ↓
ORION deterministic authorization
    ↓
(optional Soup Wall-derived narrowing checks)
    ↓
Hand
    ↓
ORION evidence verification
```

A donor security layer may **narrow** an already-authorized action, never create authority.

### Proposed falsification spike

If/when security-donor work is scheduled:

1. pin Soup Wall revision;
2. run it only against synthetic fixtures;
3. begin shadow-only;
4. test benign vs hostile tool calls;
5. test prompt-injection-tainted content driving a destructive action;
6. test secret-to-network egress;
7. test subagent permission widening;
8. test MCP manifest/tool-description mutation;
9. test approval replay / mutation / expiry;
10. test daemon missing or stale -> fail-closed behavior;
11. replay a policy change against the full reviewed corpus;
12. verify ORION remains the sole source of canonical authorization/evidence.

### ORION disposition

**HIGH-PRIORITY SECURITY DONOR / SHADOW SPIKE BEFORE ADOPTION**

---

## 3. Combined opportunity

Soup and Soup Wall together suggest a useful long-term ORION loop:

```text
real governed ORION use
        ↓
Task/Event/Hand evidence
        ↓
review + provenance
        ├──────────────→ security regression corpus
        │                    ↓
        │              policy replay/gates
        │
        └──────────────→ curated behavior dataset
                             ↓
                       detachable adapter
                             ↓
                    benchmark vs base/Qwen
```

This preserves the key V3 rule: **learning improves proposals and routing; learning never grants authority.**

## Decision recorded

- Add **Soup** to the donor map as a training/post-training candidate.
- Add **Soup Wall** to the donor map as a security/control candidate.
- Tie Soup evaluation to **V3.9A Optional personalized model adapter**.
- Do not move training ahead of the current connector + ORION product-UI build.
- Do not replace canonical memory with fine-tuned weights.
- Do not make Soup Wall an authority peer.
- Require pinned revision + synthetic falsification tests before any adoption.
