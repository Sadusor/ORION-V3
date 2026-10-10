# ORION V3 — End-of-day verified handoff
**Date:** 2026-10-10
**Scope:** Everyday PC/Android assistant, chat UI, Qwen, conversational verifier, MyGitea2 retrieval, launcher, and later autonomous HTML interface.
**Authority:** Owner → ORION policy/approval/STOP/verification → model proposals → qualified execution only. Never treat a model assertion, repository text, or a green source test as execution evidence.

## The product boundaries — permanent
- **ORION V3 everyday assistant:** Qwen local 9B, PC/phone chat, memory, documents, read-only MyGitea2 knowledge, deterministic safety. Windows candidate currently under `E:\ORION-V3-UPDATE-CANDIDATE-20261010`.
- **TheHands:** Separate, working, frozen Windows/Android remote used for owner-approved PowerShell GITCHECK/deployment tasks. Only stage designated Hand task files. Never rewrite or assimilate TheHands into ORION.
- **ORION internal Work Hands:** Different future bounded execution mechanism; no claim of unattended work until independent Windows isolation, STOP, approvals, Vault evidence and adversarial qualifications actually pass.
- **Autonomous HTML interface:** Owner has a separate HTML UI for future Qwen coordination, cloud council, code proposal/review, and ORION-internal Hands. It is NOT part of today's everyday-chat release. Cloud council/autonomous loop parity with the older development branch is not a release prerequisite.
- **MyGitea2:** Frozen local Gitea application, knowledge forge and project code/roadmap host; 127.0.0.1:3001. Git operations on an authorized repository are distinct from modifying the Gitea application.
- **Frozen canonical foundations:** Memory V1, V1.1 integrity/shadow audit, Indexed V2, canonical approval/STOP/security foundations; no edits without explicit owner consent. Module-only changes, freeze each PASS.

## Exact checkout and launch situation
- Original developer checkout: `E:\ORION-V3`, branch `spike/windows-isolation-preflight-20261008`, commit `fef1010a8c26b25752617cad7575dfbbefc1b45a`, clean at read-only preflight; preserve in place. It has different ancestry: 365 original-side and 84 candidate-side unique commits at the comparison time; NOT fast-forwardable. Do not force merge/reset, rename, replace, or assume feature parity.
- Tested everyday release checkout: `E:\ORION-V3-UPDATE-CANDIDATE-20261010`, branch main; user desktop shortcut `ORION V3.lnk` points to this candidate's `scripts\start_orion.ps1`. Shortcut installed and verified by TheHands session `e81d38778dae`; owner confirmed it launches.
- Shared persistent state is under `%LOCALAPPDATA%\ORION-V3`: canonical memory, supersession, chat history, memory candidates, Gitea code index, sidecars, pairing and logs. Both checkouts can refer to this state. Preserve it; do not copy or overwrite blindly.
- Two old scheduled ORION-V3 update tasks were observed in **Ready** state and refer to original `E:\ORION-V3\scripts\apply_orion_update.ps1`. Do not remove them without separate owner consent.
- Original remote V1 is frozen. TheHands independent. ZeroTier remains shared/manual.

## Verification timeline and evidence — TheHands results branch
Evidence is immutable JSON at `Sadusor/TheHands-` branch `thehands-results`, `docs/thehands/session-results/<session>.json`. The following references report source/runtime gates as stated, not invented tests.

1. `f74e6f907c16` PASS: responsive chat/UI candidate deployment at `2bb0cb82cb5227a012dd248c19ea3978e8dc0b50`; six conversation verifier tests, native build, stopped/restarted candidate, commit verified.
2. `3ed3e59d0060` PASS: minimize/restore control fix, native candidate build and backend commit `6bb6f2cc1f5eb029c77de84819273f9f78aef321`; user subsequently reported other UI features good and identified a minimized-card defect addressed by fix.
3. `5a47c1c63977` PASS read-only promotion preflight: original commit `fef1010`, candidate `6bb6f2c`, shared-state inventory, clean tracked trees, ~669.9 GB free E:.
4. `cc08d6e4040e` FAIL attempted main promotion: `Main not fast-forwardable`. It stopped BEFORE overwriting or stopping ORION.
5. `3476cb097c47` PASS ancestry diagnostic: merge base `be618edb8cd40a7e5da0210ef1b4599a0cfbf220`, 365/84 divergent commits. Owner decided NOT to replace the original checkout; standalone launcher approach chosen.
6. `4380450dde74` PASS read-only paths audit: candidate self-locating start/stop scripts, original updater scheduled tasks exist, backend and candidate UI running.
7. `e81d38778dae` PASS: desktop `ORION V3.lnk` launcher created, points to release candidate, legacy installation and scheduler untouched. Owner physically confirmed launcher works.
8. `46fa6880e88d` PASS: V2 conversation source worktree, 11 tests; no runtime restart.
9. `f3f1cd9dd32e` PASS: V2 source fast-forward to `b3d5bd46fb9c3a2bd57f61955cd0a14989903f24`, 11 tests, runtime not restarted.
10. `29f73de4426c` FAIL native V2 update request when backend offline; no updater executed. `8cb3930eaa2e` FAIL subsequent update preflight because running backend already reported new V2 source commit. Neither proves native rebuild.
11. `1047b5f6d6b6` PASS read-only identity check: backend/source at `b3d5bd4`, native build still `6bb6f2c`; historical update-status file must NOT be read as V2 build evidence.
12. **Owner real Qwen V2 acceptance:** ordinary explanatory question on Git push and TheHands had NO failed-verification warning; Qwen explicitly declined an unauthorized Git push. This qualifies intended conversational distinction in those observed cases, not a blanket security certification.
13. `63817b139f67` FAIL STRATA test suite after staging smooth stream: boot test `MutationObserver is not defined`; JS syntax passed. `ff40431dc427` PASS diagnostic reproduces same boot failure at PRE-STREAM V2 baseline, establishing it predates stream change.
14. `31cd3aa390b9` FAIL streaming build preflight due to script incorrectly requiring old runtime to equal new source commit; no stop/build.
15. **`50f3712cc6b5` PASS actual final deployment:** candidate STOP PASS; native Windows build `eaac25d85fa329ffcd6c7c2d50e30bf87892f501`; RUNNING_COMMIT same. Final source change solely `ui/strata/modules/live-brain-chat.js`. Owner reports smoother presentation, asks to end here. Source updates now deployed; visual feedback positive, no claim of literal token-at-a-time network streaming.
   
## Conversational Verifier V2
- New isolated `src/orion_v3/modules/conversation_verifier_v2.py`, wired via `gitea_chat_brain_v1.py`, tested `tests/test_conversation_verifier_v2.py` plus six V1 cases = 11/11.
- Intent: informational/explanatory chat can disclose semantic uncertainty rather than block an entire answer when no precise unsupported claim is established; deterministic executable-response preflight and action-request strict checks remain.
- Limitations: V2 remains rule-based, false negatives/positives possible. Do not say this is verified autonomous execution or a fully proven truth checker. One early response described a historic Gitea authentication failure as recent; better retrieval freshness needed.
- **Owner direction:** Freeze V2 after today's accepted conversation test; future fixes through independent modules unless necessary and expressly approved.

## Chat UI and streaming
- Isolated chat reading controls and CSS provide minimize/restore, resize, status-panel toggle, alert panel controls and expanded chat. Observed UI checks mostly good.
- Existing Ollama stream supplies accumulating `brain_stream_preview`. `live-brain-chat.js` now displays **already received** text progressively via animation frames. It does not generate extra text, change model behavior, or bypass verification.
- Original full STRATA no-browser boot suite has an environment error `MutationObserver is not defined` on BOTH old and new baselines; isolated JS parse and source contracts PASS. Track harness fix separately; do not edit frozen UI simply to silence it.
- Final release code and backend+native build at `eaac25d` proven in TheHands session `50f3712cc6b5`. Owner reports UI streaming better. Freeze stream module after acceptance; avoid further cosmetic churn.
- Windows desktop build proof is NOT an Android UI/APK streaming qualification. Android behavior remains to be verified separately if wanted.

## Everyday knowledge and MyGitea2
- Working pieces: Qwen 9B chat, canonical memory/context, chat history, read-only Gitea project retrieval components, bounded code index and retrieval contracts. Existing physical checkpoint/document retrieval occurred in past sessions. Do not overclaim universal cross-repository search or current count of repos from a first page of 50.
- Open: fresh roadmap/current commit tracking, follow-up source citations, broad actual source search coverage, English/Greek cross-language semantic retrieval, permanent attached-document indexing/storage across restarts, unified retrieval ranking/scope, and correct verifier access to Qwen's actual provenance.
- The answer on 2026-10-10 about Git push/TheHands was good, but longer model explanation still portrays Gitea and verifier too conservatively or inaccurately (e.g. verification always before model text), and can conflate historical state with current reality. Fix evidence supply/freshness rather than hard-code model claims.
- MyGitea2 repository branch `orion-checkpoint-20261010` is NOT automatically GitHub main; older checkpoint content can be stale. Publication requires authenticated normal Git push verified by remote ref. Never edit Gitea DB/app, never force-push main, never leak tokens.

## Next roadmap in owner-approved order
1. Stop for today; no more changes to accepted chat V2 and stream modules.
2. Publish this checkpoint to **a new non-force MyGitea2 branch**, verify remote branch commit, leave Gitea main and the old pinned checkpoint branch intact. No successful publication claim before live Git evidence.
3. On next session: Universal Retrieval Interface V1 as a separate module: provenance, freshness, scopes, source priority and bounded response context, covering memory, Gitea and permanent documents.
4. Fix real MyGitea2 search and stale checkpoint sync; query through normal chat, cite exact branch/path/commit, don't falsify repo count or current state.
5. Persistent document ingestion and retrieval through existing Windows/Android chat; Greek/English retrieval benchmark and incremental indexing.
6. Separate owner-provided autonomous HTML UI later: Qwen proposer/coordinator, optional cloud council/code specialists, ORION-owned approval/STOP/Vault evidence, internal Work Hands only after isolation authorization qualification. No TheHands integration into ORION.

## Operational rules
- Never claim a GitHub commit means target Windows execution. Fetch TheHands `thehands-results` JSON and read `output_tail`.
- No destructive reset/merge of original diverged checkout. Preserve original and shared local state.
- For upcoming source work, only edit new bounded modules; freeze after observed PASS; GITCHECK evidence numbers required.
- Prefer rapid targeted tests and real user chat examples to repeated unnecessary full builds. Separate source PASS, runtime PASS and UX acceptance.
