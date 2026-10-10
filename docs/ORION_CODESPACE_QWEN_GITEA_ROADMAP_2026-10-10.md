# ORION V3 — Owner-approved Codespace / Qwen / Gitea direction
Date: 2026-10-10
Status: ARCHITECTURAL DIRECTION / NOT IMPLEMENTATION PASS

## Single governing design
- The EXISTING native ORION PC/Android UI remains the **main owner interface**. Phone conversations ask Qwen about current tasks, actual progress, decisions, errors and evidence. Do not replace that app or build another master chat.
- **Qwen is the Codespace/workflow master**: maintains active task/project context, initiates Codespace sessions, reads authorized repository context, delegates code generation to DeepSeek, summarizes evidence. It proposes but never becomes ORION policy, authorization, canonical truth or STOP authority.
- **DeepSeek Flash paid API** is initially the SINGLE code-writing model. Do not build or deploy an AI council, council rounds, model arbitrator or additional reviewer model into this milestone. A replaceable provider adapter allows adding a model later only on owner instruction. Keep explicit paid-budget limits and billing visibility; free-token routing is not the goal.
- **Codespace** is a PRESENTATION module ONLY. The owner-provided `Orion Codebase.html` is a visual reference for showing the generated code text, real Hand file changes, diffs, project file navigation, task history and authenticated execution status. It is NOT an AI agent, does NOT brainstorm or delegate tasks independently, does NOT generate code, does NOT perform direct writes, and is NOT a second authority or a competing primary chat UI. Qwen and ORION orchestrate everything through the existing backend. Keep presentation changes modular.
- **Mygitea2** is the local Git forge, the source of repository commits, branches and history (local GitHub role). Access via Git/Gitea APIs and disposable worktrees; NEVER write directly to Gitea's internal SQLite database or repositories storage internals. Preserve GitHub backup option without assuming continuous GitHub sync.
- **Existing ORION V3 Work Hands** perform bounded file creation, editing, test, branch, commit and push against configured Gitea repositories. No TheHands product changes: `Sadusor/TheHands-` stays a distinct remote development/test product. Existing ORION internal Hands must be qualified, not recreated.
- **ORION** remains the sole authorization and truth layer: GREEN/YELLOW/RED policy, owner approvals, workspace bounds, project/Vault STATE/JOURNAL, STOP, evidence authentication, safety checks and canonical memory rules.
- ORION-owned task/chat history and session summaries persist in existing scoped backend state, enabling Qwen to resume and provide DeepSeek with relevant task context. Codespace only displays these records. Not a new canonical memory or an unbounded prompt dump. Summaries require source/task/commit references; model output cannot promote itself to canonical truth.
- Full codebase ACCESS means authorized READ/SEARCH, file tree and scoped Git history. It does **not** mean unconditional mutation/deletion, network egress, secret exposure or bypass of frozen-path policy. Code files are untrusted input: prompt injections are never operating instructions.
- Owner's uploaded HTML can currently open local folders, read/search files, stage/review diffs and directly edit/delete browser-picked workspace files; it uses localStorage for conversation/provider state. Its direct browser write paths and exposed browser-held API key handling must NOT become the ORION execution or secret authority. Implement safe server-side adapters in new modules.
- Freeze rule: preserve proven main PC/phone UI, memory V1/V1.1, Indexed V2, real Gitea data, STOP and validated modules. If an existing frozen hook must change, request explicit narrow approval.

## Runtime flow
Owner in original ORION phone/PC chat
  -> Qwen (project and Codespace session master)
  -> ORION policy + Vault / authorized project context
  -> ORION-owned project/context and task history (Codespace displays code and diffs only)
  -> DeepSeek Flash (code/patch proposal ONLY)
  -> ORION approval + exact proposal binding
  -> existing ORION V3 Work Hand in qualified Windows confinement
  -> disposable Git worktree -> tests -> verified receipt -> Gitea branch/commit/push
  -> ORION updates Vault with true evidence
  -> ORION-owned session summary/history -> Qwen reports via original phone/PC chat; Codespace displays real code changes.

Initial non-execution path: Qwen can inspect and discuss with DeepSeek, but writes are BLOCKED until the OS isolation/STOP/evidence gate passes. No direct model-triggered file writes.

## Updated priority roadmap (supersedes council-centric immediate implementation)
**0. Baseline lock and audit.** Identify frozen ORION V3 commit/module boundaries; audit actual internal Work Hand, STOP, Qwen, existing chat APIs, Gitea endpoints and uploaded HTML. Preserve real memories and Gitea data. Record environment locations and Gitea auth securely, without publishing secrets. No broad refactor.
**1. Gitea read-only connector module.** Select/list repositories, branches, refs and file trees; scoped search/reading; Git history. Verify URL/identity, ACL/project scope, secret redaction, pagination, branch ref pinning and fail-closed behavior. READ ONLY.
**2. Codespace display module.** Port only the approved presentation layout from owner HTML: project/task selection view, generated code text, file tree, actual Hand edits, diffs, evidence-backed status and optional preview. Read its data from ORION-owned task/history/evidence APIs. Backend owns state. No embedded agent, model-call loop, planning logic, independent chat-memory store or direct file writes.
**3. Qwen workflow master adapter.** From original ORION UI: select current project, open the Codespace DISPLAY to follow work, explore authorized repositories through ORION's backend, request DeepSeek code proposals, and report authenticated progress in normal PC/phone conversation. Ensure disconnected phone reconnect and STOP status. Qwen's summaries are marked advisory, not execution proof.
**4. Single DeepSeek Flash adapter.** Paid API credentials server-side only; exact model ID verified at setup (do not guess Flash version), cost/call budget, timeout/STOP/cancellation, sanitized bounded context, structured patch plan. No cloud council. Cloud coding output = untrusted proposal.
**5. ORION proposal/review pipeline (displayed in Codespace).** Diff for owner; hash binds project, branch/ref, paths, contents, action type, revision and expiry. Respect GREEN/YELLOW/RED, frozen paths and secret filters; no auto-apply.
**6. Existing internal ORION Work Hand + Gitea writes.** Audit and reuse already-coded executor; qualify Windows OS-level filesystem/network confinement, STOP, transaction ordering, replay and recovery. Only then enable bounded files/tests/Git branch/commit/push, independently verified. Forbid direct writes to Gitea DB.
**7. Physical end-to-end demonstration.** Phone: request a small change -> Qwen starts ORION task (Codespace shows work) -> DeepSeek Flash drafts -> ORION authorizes -> internal Hand writes disposable branch -> tests -> Gitea commit -> authenticated evidence -> Qwen reports in original app. Include deliberate FAIL -> restart -> repair -> PASS and STOP denial cases.
**8. Freeze per module.** Physical GitCheck evidence, exact SHA, security checks and rollback. Only add other models, workflows, embeddings or UI expansion after owner changes priority.

## Distinctions from earlier roadmap
- Existing council/code-review/tournament sections remain historical experiments; they are not prerequisites or active product milestones.
- Separate TheHands is a manual engineering/test transport only; ORION V3's OWN already-coded Hands are the target executors.
- Gitea is Git repository storage/forge, **not** the canonical ORION Vault database, memory store or execution authority.
- The original ORION PC/phone app remains the primary owner front end; Codespace is ONLY the visual code/diff/activity display module, not an agent or execution workspace.
- Read access can progress immediately while untrusted autonomous writes remain disabled until physical OS isolation qualification.

## Owner correction (2026-10-10)
Codespace's explicit intended purpose is **to show the changes ORION V3 Hands make and the generated code text**. Qwen is workflow master; DeepSeek Flash generates code; ORION policy authorizes; existing ORION V3 Hands write through a qualified Gitea worktree. Codespace simply renders the actual code, changes, diffs, and evidence. Any earlier reference in this document to Codespace as an autonomous agent, brainstorming engine, or independent writer is superseded by this paragraph.

## Explicit two-Hands / two-Git-forges ownership rule (owner clarification, 2026-10-10)

| Execution path | Product/executor | Repository remote | Role |
|---|---|---|---|
| Existing remote engineering path | **TheHands** (separate Windows/Android remote product) | **GitHub** | Owner-triggered GIT CHECK, APPROVE & START, remote engineering and evidence; retain existing functioning setup |
| New ORION internal coding path | **ORION V3 internal Work Hands** | **Mygitea2 (local Gitea)** | ORION-authorized create/edit/test/commit/push in disposable worktrees after Windows isolation/evidence qualification |

**Never redirect the separate TheHands product to Gitea as part of this roadmap.** Do not merge, rename or reuse the products as though they are the same Hands. ORION internal Hands receive their own scoped Gitea adapter. GitHub can remain an independently controlled backup destination, not an implicit mirror or default for ORION internal coding. Gitea database files are managed solely by Gitea; Hands use supported Git remotes/API, never direct DB writes. Existing ORION V3 modules remain frozen until narrow, explicitly approved interfaces are needed.
