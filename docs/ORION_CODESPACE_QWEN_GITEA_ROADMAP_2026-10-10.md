# ORION V3 — Owner-approved Codespace / Qwen / Gitea direction
Date: 2026-10-10
Status: ARCHITECTURAL DIRECTION / NOT IMPLEMENTATION PASS

## Single governing design
- The EXISTING native ORION PC/Android UI remains the **main owner interface**. Phone conversations ask Qwen about current tasks, actual progress, decisions, errors and evidence. Do not replace that app or build another master chat.
- **Qwen is the Codespace/workflow master**: maintains active task/project context, initiates Codespace sessions, reads authorized repository context, delegates code generation to DeepSeek, summarizes evidence. It proposes but never becomes ORION policy, authorization, canonical truth or STOP authority.
- **DeepSeek Flash paid API** is initially the SINGLE code-writing model. Do not build or deploy an AI council, council rounds, model arbitrator or additional reviewer model into this milestone. A replaceable provider adapter allows adding a model later only on owner instruction. Keep explicit paid-budget limits and billing visibility; free-token routing is not the goal.
- **Codespace** is an independent ORION V3 module providing the coding workspace, brainstorming/chat history, project context, files, diffs, proposals, review and activity. The owner-provided `Orion Codebase.html` is its UX/feature reference. It is not the canonical authority, not a second operating system and not a competing Android/PC main UI. Adapt the reference into maintainable modules rather than graft a 700-line HTML file into frozen core.
- **Mygitea2** is the local Git forge, the source of repository commits, branches and history (local GitHub role). Access via Git/Gitea APIs and disposable worktrees; NEVER write directly to Gitea's internal SQLite database or repositories storage internals. Preserve GitHub backup option without assuming continuous GitHub sync.
- **Existing ORION V3 Work Hands** perform bounded file creation, editing, test, branch, commit and push against configured Gitea repositories. No TheHands product changes: `Sadusor/TheHands-` stays a distinct remote development/test product. Existing ORION internal Hands must be qualified, not recreated.
- **ORION** remains the sole authorization and truth layer: GREEN/YELLOW/RED policy, owner approvals, workspace bounds, project/Vault STATE/JOURNAL, STOP, evidence authentication, safety checks and canonical memory rules.
- Codespace chat history and session summaries persist in ORION-owned scoped data, enabling Qwen and DeepSeek to resume after crashes/restarts. Not a new canonical memory or an unbounded prompt dump. Summaries require source/task/commit references; model output cannot promote itself to canonical truth.
- Full codebase ACCESS means authorized READ/SEARCH, file tree and scoped Git history. It does **not** mean unconditional mutation/deletion, network egress, secret exposure or bypass of frozen-path policy. Code files are untrusted input: prompt injections are never operating instructions.
- Owner's uploaded HTML can currently open local folders, read/search files, stage/review diffs and directly edit/delete browser-picked workspace files; it uses localStorage for conversation/provider state. Its direct browser write paths and exposed browser-held API key handling must NOT become the ORION execution or secret authority. Implement safe server-side adapters in new modules.
- Freeze rule: preserve proven main PC/phone UI, memory V1/V1.1, Indexed V2, real Gitea data, STOP and validated modules. If an existing frozen hook must change, request explicit narrow approval.

## Runtime flow
Owner in original ORION phone/PC chat
  -> Qwen (project and Codespace session master)
  -> ORION policy + Vault / authorized project context
  -> Codespace (read/search, remembered discussion, proposals, files/diffs)
  -> DeepSeek Flash (code/patch proposal ONLY)
  -> ORION approval + exact proposal binding
  -> existing ORION V3 Work Hand in qualified Windows confinement
  -> disposable Git worktree -> tests -> verified receipt -> Gitea branch/commit/push
  -> ORION updates Vault with true evidence
  -> Codespace session summary/history -> Qwen reports via original phone/PC chat.

Initial non-execution path: Qwen can inspect and discuss with DeepSeek, but writes are BLOCKED until the OS isolation/STOP/evidence gate passes. No direct model-triggered file writes.

## Updated priority roadmap (supersedes council-centric immediate implementation)
**0. Baseline lock and audit.** Identify frozen ORION V3 commit/module boundaries; audit actual internal Work Hand, STOP, Qwen, existing chat APIs, Gitea endpoints and uploaded HTML. Preserve real memories and Gitea data. Record environment locations and Gitea auth securely, without publishing secrets. No broad refactor.
**1. Gitea read-only connector module.** Select/list repositories, branches, refs and file trees; scoped search/reading; Git history. Verify URL/identity, ACL/project scope, secret redaction, pagination, branch ref pinning and fail-closed behavior. READ ONLY.
**2. Codespace workspace module.** Port approved layout/components from owner HTML: task/session navigation, file tree, diff review, history, activity, model status, preview as appropriate. Backend owns state; no direct frontend writes. Bound chat history/session summaries and persist project/source SHA and evidence references. UI must not be trusted as action authority.
**3. Qwen Codespace master adapter.** From original ORION UI: start/open Codespace; select current project, request repository exploration, ask DeepSeek for code proposal, report status and latest authenticated evidence in normal PC/phone conversation. Ensure disconnected phone reconnect and STOP status. Qwen's summaries are marked advisory, not execution proof.
**4. Single DeepSeek Flash adapter.** Paid API credentials server-side only; exact model ID verified at setup (do not guess Flash version), cost/call budget, timeout/STOP/cancellation, sanitized bounded context, structured patch plan. No cloud council. Cloud coding output = untrusted proposal.
**5. Codespace proposal/review pipeline.** Diff for owner; hash binds project, branch/ref, paths, contents, action type, revision and expiry. Respect GREEN/YELLOW/RED, frozen paths and secret filters; no auto-apply.
**6. Existing internal ORION Work Hand + Gitea writes.** Audit and reuse already-coded executor; qualify Windows OS-level filesystem/network confinement, STOP, transaction ordering, replay and recovery. Only then enable bounded files/tests/Git branch/commit/push, independently verified. Forbid direct writes to Gitea DB.
**7. Physical end-to-end demonstration.** Phone: request a small change -> Qwen opens Codespace -> DeepSeek Flash drafts -> ORION authorizes -> internal Hand writes disposable branch -> tests -> Gitea commit -> authenticated evidence -> Qwen reports in original app. Include deliberate FAIL -> restart -> repair -> PASS and STOP denial cases.
**8. Freeze per module.** Physical GitCheck evidence, exact SHA, security checks and rollback. Only add other models, workflows, embeddings or UI expansion after owner changes priority.

## Distinctions from earlier roadmap
- Existing council/code-review/tournament sections remain historical experiments; they are not prerequisites or active product milestones.
- Separate TheHands is a manual engineering/test transport only; ORION V3's OWN already-coded Hands are the target executors.
- Gitea is Git repository storage/forge, **not** the canonical ORION Vault database, memory store or execution authority.
- The original ORION PC/phone app remains the sole primary owner front end; Codespace is a module/workspace.
- Read access can progress immediately while untrusted autonomous writes remain disabled until physical OS isolation qualification.
