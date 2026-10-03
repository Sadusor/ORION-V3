# ORION V3 — Fresh Chat Handoff — 2026-10-03 14:23 Europe/Athens

Status: **DOCUMENTED STOP POINT — NO NEW UNTESTED EXECUTION SLICE STAGED**

## Read first in a new chat

1. `AGENTS.md`
2. `docs/ORION_SYSTEM_MODEL.md`
3. `docs/STATUS.md`
4. `docs/ROADMAP.md`
5. this handoff

Then inspect the exact branch heads before changing code.

---

## 1. Authoritative architecture

ORION is not one agent.

```text
USER
 -> ORION-owned interface
 -> ORION CORE
    - canonical Memory
    - Task / Attempt / Event state
    - semantic Intent + deterministic canonicalization/resolution
    - Capability Registry / policy / authority
    - approvals / leases / Stop
    - local Event Exchange
    - evidence / verifier
 -> replaceable execution/reasoning paths
```

Hard rule:
`models propose; ORION owns authority, state, evidence and acceptance`.

Lightweight assistant path:
`Qwen literal semantics -> ORION canonicalizer -> deterministic resolver -> policy -> vetted Hand`.

Coding Factory target:
`bounded TaskPacket -> cloud coder -> immutable WorkPackage -> independent review -> ORION decision -> approved Hand -> verifier -> result`.

Whole-PC agent remains a later escalation Hand for novel GUI work only.

---

## 2. Proven lightweight governor

V3-RUN-014 physically validated the current semantic architecture on the 32-case corpus:
- Qwen3.5-9B one turn / zero tools;
- native Ollama JSON mode;
- literal semantic intent/entities;
- deterministic ORION canonicalization;
- deterministic intent -> capability resolution;
- safe non-dispatch hard gate;
- low token/latency thresholds passed.

Do not revert to direct Qwen capability selection.

---

## 3. Proven canonical Memory / continuity

V3-RUN-015 exact tested code SHA:
`b800de5659ce74e3b52b88e41f4af53a5b6eacfd`

Observed:
`64 passed in 1.00s`

Physically proven:
- SQLite authoritative state;
- deterministic immutable Event hashes;
- DB triggers deny Event UPDATE/DELETE;
- project/task scoping;
- Memory requires real provenance Event;
- cross-project provenance denied;
- silent current-Memory overwrite denied;
- explicit supersession preserves old record;
- L0/L1/L2 bounded retrieval;
- close/reopen persistence;
- no model/network donor runtime required.

Memory principle:
raw PASS/FAIL/history is Evidence first; promotion to canonical Memory is explicit.

Embeddings/vector search remain derived/rebuildable, not truth.

---

## 4. Proven local AI <-> ORION <-> Hands exchange

V3-RUN-016 exact tested code SHA:
`0f77a8e07da6936e811936b50a1d201887a1ca93`

Physically proven:
- idempotent external-message ingestion;
- collision with different immutable content denied;
- recipient inbox;
- separate append-only acknowledgement receipts;
- Event is never mutated by acknowledgement;
- causal `PROPOSAL -> REVIEW -> DECISION -> ACTION -> EVIDENCE -> RESULT` chain;
- cross-task parent denied;
- bounded project/task packet;
- close/reopen persistence;
- no GitHub/network/model dependency.

GitHub remains source control and optional remote transport; the local Event Exchange is the future live mailbox.

---

## 5. ORION Remote transport is fixed and separate from V3

Do not describe ORION Remote as 'converted to V3'.

Separate systems:
```text
Sadusor/Orion
  ORION Remote / operator / exact-SHA transport
        |
        | named task + data-only V3_GATE.json
        v
Sadusor/ORION-V3
  ORION Core under development
```

Remote activation physical PASS:
- Remote SHA: `98b1a78beb3edcab95f7dfe22fbf4b87d7c3580e`
- attempt 417 PASS;
- primary sole-named-task route probe PASS;
- multiple named tasks auto-route DENIED;
- exact Remote SHA sync PASS;
- Windows restart handoff PASS.

V3-RUN-017 named-task transport PASS:
- named task: `v3-current-gate`;
- session: `8ba1ec0b741c`;
- result: PASS.

Normal owner workflow is now:
`CHECK GITHUB -> APPROVE & RUN`.

Do not make the owner paste PowerShell for normal V3 gates.

---

## 6. Coding Factory WorkPackage foundation — newest physical PASS

V3-RUN-018 exact tested V3 SHA:
`6ef6e9ccd3bea7a9e56c5761173ed76609c47ddc`

Remote staging SHA:
`4544acdd1aebb23769392eff9bd4dc5f78e8dc68`

Named session:
`3c93b3f33491`

Observed regression:
`77 passed in 3.02s`

Observed gate:
```text
ARTIFACT_DEDUPLICATION> PASS
ARTIFACT_TAMPER_DETECTION> PASS
DETERMINISTIC_PACKAGE_IDENTITY> PASS
PACKAGE_MANIFEST_RELOAD> PASS
OUT_OF_SCOPE_FILE> DENIED
OUT_OF_SCOPE_PATCH_TARGET> DENIED
NON_EXACT_BASE_SHA> DENIED
PACKAGE_BOUND_REVIEW_DECISION_CHAIN> PASS
CANDIDATE_EXECUTION_AUTHORITY> NONE
CROSS_PACKAGE_REVIEW_REUSE> DENIED
PACKAGE_BLACKBOARD_REOPEN_PERSISTENCE> PASS
NETWORK_MODEL_EXECUTION_DEPENDENCY> NONE
CODING_FACTORY_WORKPACKAGE_GATE> PASS
STATUS> PASS
```

New V3 code:
- `src/orion_v3/coding_factory/artifacts.py`
- `src/orion_v3/coding_factory/workpackage.py`
- `src/orion_v3/coding_factory/blackboard.py`
- `tests/test_coding_factory_workpackage.py`
- `docs/contracts/CODING_FACTORY_WORKPACKAGE.md`

Current WorkPackage V0 intentionally has only PATCH/FILE candidate artifacts.

It has NO command execution, NO worktree mutation, NO cloud call, NO Action Lease and NO execution authority.

PATCH artifacts must declare target paths and those paths are checked against allowed/forbidden project scope before the package is accepted.

---

## 7. Current repository state at handoff

ORION-V3 active branch:
`agent/v3.1-openjarvis-tools`

Latest physically tested code SHA:
`6ef6e9ccd3bea7a9e56c5761173ed76609c47ddc`

After that test, only documentation/status/roadmap commits were added.

Pre-handoff documentation head:
`86c0baf6e5c180f5d28e50c41ed2b44ac3a5e90f`

Legacy ORION Remote branch:
`agent/coding-mode-github-loop-v0`

Remote source branch currently has `V3_GATE.json` for V3-RUN-018.

Frozen fallback remains:
- branch: `checkpoint/2026-10-01-orion-remote-project-link`
- SHA: `327d32f714129ca633517a8f4158cd84820c1504`

Never modify the frozen fallback.

---

## 8. Existing provider/reviewer infrastructure — reuse, do not reinvent

Legacy ORION already has:
- `provider_vault.py` with Windows DPAPI Current User secret storage;
- dynamic provider records for Groq/Gemini/OpenAI-compatible;
- `reviewer_connector.py` with Ollama/Groq/Gemini/vault discovery;
- independent reviewer runs;
- provider/model identity + usage evidence;
- Reviewer Exchange storage;
- cloud egress still explicit/policy-controlled.

Provider/reviewer results are advice only and never mint Hand authority or verifier PASS.

When Coding Factory reaches real cloud calls, adapt/reuse these contracts rather than creating new provider-specific clients.

---

## 9. Exact next engineering sequence

### V3-RUN-019 — Attempt / lease / checkpoint / Stop ownership

Build the minimal durable execution ownership layer before WorkPackages can touch code.

Must prove at least:
- one active lease owns an Attempt;
- second worker cannot claim active Attempt;
- checkpoint/update requires matching lease;
- expired/revoked/lost lease cannot advance the Attempt;
- Stop invalidates execution ownership before further effects;
- stale late worker/result cannot silently advance state;
- restart/reopen preserves recoverable task/attempt truth.

Use OpenMuse lease/checkpoint patterns as donor inspiration, but ORION owns the authority contract.

### V3-RUN-020 — isolated exact-SHA WorkPackage execution envelope

After RUN-019 passes:
- create disposable Git worktree at exact approved base SHA;
- verify HEAD and clean state;
- load immutable WorkPackage by ID/hash;
- mechanically apply one harmless PATCH/FILE artifact;
- verify only allowed paths changed;
- capture exact Git diff/hash/evidence;
- run a tiny deterministic verifier;
- clean worktree on PASS/FAIL/Stop;
- no push/merge.

### Then: PC coding-agent benchmark

YES, benchmark a mature coding agent / semantic Coding Hand on the PC.

Do it only after the ORION execution envelope exists so every candidate is judged under the same authority/evidence rules.

Use the same small bounded coding case and measure:
- exact task success;
- allowed-path compliance;
- unexpected mutations;
- Stop/cleanup;
- tests/verifier result;
- diff quality/evidence;
- latency/resource overhead;
- whether it can operate as a replaceable Hand without taking Task authority.

Candidates already relevant from prior work:
- OpenHands / Software Agent SDK;
- Claude Code-style coding Hand;
- OpenJarvis-native orchestration only if it adds measurable value.

V3-RUN-008 already physically qualified OpenHands FileEditor and Windows Terminal mechanics as Hands-only building blocks, but that was NOT an autonomous coding-agent benchmark.

Do not choose an agent by hype. Qualify candidates on the same bounded case.

### After execution/agent gates

Connect real cloud coder/reviewer workflow:
`TaskPacket -> coder WorkPackage -> reviewer -> ORION decision -> approved Hand -> verifier -> result -> optional next attempt`.

Human should only be needed for meaningful approval, ambiguity, policy or blocked decisions.

---

## 10. Things NOT to do next

- do not reopen the direct Qwen capability-router design;
- do not add a giant regex parser;
- do not add embeddings before deterministic retrieval needs them;
- do not connect cloud AI directly to arbitrary shell;
- do not let WorkPackage acceptance equal execution permission;
- do not benchmark agents before a common ORION execution envelope exists;
- do not replace the proven Remote transport while building Coding Factory;
- do not use GitHub Actions / paid CI for these gates;
- do not claim PASS without physical evidence.

---

## 11. Resume sentence

Fresh chat should begin with:

> Read the 2026-10-03 fresh-chat handoff and current STATUS/ROADMAP. V3-RUN-018 physically passed. Start from V3-RUN-019 Attempt/lease/checkpoint/Stop ownership. Do not redesign the proven semantic governor, Memory/Event Exchange, Remote named-task transport, or WorkPackage foundation.
