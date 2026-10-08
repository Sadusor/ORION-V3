# ORION V3 — FROZEN CLOUD → LOCAL QWEN BASELINE (2026-10-08)

Status: **PHYSICAL PASS — FROZEN EXPERIMENTAL BASELINE**. This is a tested advisory pipeline, **not** production autonomy.

## Exact evidence
- Physical session: `e00f23a8b5c0`; published result **PASS**; test runner revision `e73ca86bf2b045eb6c3f9fb8098896d26eed18c3`.
- ORION V3 source revision tested: `d83b4c91c4254d78fdce2b75ced5155ab9724902` on `spike/windows-isolation-preflight-20261008`.
- GPT-OSS 120B (Groq): complete, nonempty output.
- Qwen 3.8 27B (Groq): complete, nonempty output.
- GPT-OSS 20B (Groq): complete, nonempty output.
- Local Ollama `qwen35-9b-orion:latest`: generated synthesis with `think:false`, output budget 1000.
- Saved local advisory: `C:\Users\SouS\AppData\Local\Orion\coding-mode\coding-mode\work-loop-evidence\council-1791489172.json`.
- Evidence schema: `orion.v3.council.advisory.v1`; records cloud response hashes, proposal, `approval: NOT_GRANTED`, `execution: NOT_PERFORMED`.
- Console activity was requested for cloud reviewers; no separately qualified Qwen or ORION native Hand console.
- Physical run verified via published result and log, not by reading proposal content. Do **not** claim proposal quality, independent verification, native execution, or Vault transaction PASS.

## How we got here
1. Original ORION provider connector and DPAPI-backed provider vault were discovered and reused; no API-key reentry.
2. Gemini repeatedly returned errors, and preview endpoints returned reported HTTP 404. Catalog availability did not imply successful requests.
3. Five-reviewer tests stalled or timed out. Unfit specialty models were selected by overly broad catalog filters. Owner used STOP; physical session `4eb3041c82bd` recorded STOPPED.
4. Session `47686aa01493`: five-model test timed out. Later tests reduced to three qualified candidates, excluding Gemini.
5. Session `3450d16879f0`: two cloud responses usable, local Qwen HTTP error.
6. Session `27cc4a1d882d`: one cloud response usable, Qwen runtime error.
7. Session `cf02e92908c3`: Ollama Qwen 9B installed; thinking nonempty but final response empty.
8. Setting `think:false`, using installed `qwen35-9b-orion:latest`, and adequate output budget led to physical PASS `e00f23a8b5c0`.

## Freeze rules
- Treat the above source revision and session as the immutable reference. No in-place changes to its behavior without a new isolated module, explicit comparison and evidence.
- The existing ORION V1 Remote and frozen Memory modules remain untouched.
- Keep cloud outputs **untrusted advisory data**. Qwen is a synthesizer, not an approver or executor.
- ORION alone owns authorization, STOP, state, evidence and verification.
- No automatic execution or PASS promotion from model text.
- Distinguish remote engineering transport from ORION's own Work Hand. The separate **TheHands** product is **not** an ORION dependency, module, authority, Hand, code donor or required workflow. Do not route future ORION module development through that repository. Historical external runner evidence remains provenance only.

## Next precise milestone
1. Add a separate ORION-native **Qwen visibility console** with truthful stage/output/error indicators; medium-size ordered window layout and guaranteed child cleanup.
2. Implement ORION-owned proposal handoff: load saved advisory, validate schema, hashes and provenance; translate to bounded typed Proposal; reject prompt injection, unauthorized scope, missing owner approvals.
3. Dry-run `STATE -> Qwen proposal -> ORION authorization -> simulated/native Hand contract -> independent verifier -> STATE/JOURNAL`; fail closed on missing evidence.
4. Qualify physical Windows confinement and STOP (filesystem and network; full combined gate outstanding) **before** native writes.
5. Physically prove owner-approved FAIL -> restart -> fresh Qwen repair -> independently verified PASS -> Vault update. Add UI/phone supervision afterward.

## Next-chat instruction
Read this file first, then `docs/STATUS.md`, `docs/ROADMAP.md`, `docs/decisions/0018-orion-only-engineering-collaboration-loop.md`, and actual `src/orion_v3/work_loop/` contracts. Work only on `Sadusor/ORION-V3` experimental branch. Check exact GitHub state and physical evidence before claiming anything. Do not infer a successful execution from the advisory PASS.
