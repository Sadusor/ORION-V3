# ORION V3 — Autonomous Development Loop: Approved Design and Execution Ledger
Date: 2026-10-12
Status: DESIGN AGREED; IMPLEMENTATION NOT YET VERIFIED
Branch: docs/autonomous-loop-plan-20261012

## Mission
ORION V3 is the sole governance, canonical state, verification, STOP and recovery authority for an autonomous coding team. Owner sets goals and exceptions; Qwen 9B acts as project manager (not programmer); paid DeepSeek Flash writes code and makes final technical decisions; a free cloud model independently reviews; ORION internal Hands execute bounded operations and real tests; MyGitea2 stores branches/commits/evidence; ORION memory supplies scoped project context; Claude-designed writing UI displays all agent conversation, revisions, logs and history; ORION Android offers control, approvals, notifications and STOP.

DeepSeek's final *technical* decision never overrides ORION policy, owner permissions, protected branches, budgets or verified evidence.

## Non-negotiable boundaries
1. Module-only development: no broad refactors or modification of passing/frozen modules. Add adapters/sidecars. Any exceptional tiny edit requires explicit owner permission.
2. After each step, record evidence and status: NOT STARTED, IN PROGRESS, PASS, FAIL, BLOCKED. PASS requires concrete command, revision, log and acceptance evidence. Freeze passed module and document its interface.
3. TheHands- is a SEPARATE frozen Windows/Android remote used to drive manual PowerShell and GITCHECK on E:. Do not integrate its runtime into ORION or modify its source without explicit owner authorization. ORION's INTERNAL Hands are the target autonomous executor.
4. Remote V1 remains frozen fallback. Keep ORION canonical memory V1/V1.1/Indexed V2 unchanged. Project-scoped read-only context compilation; promotion only through existing owner-governed rules.
5. Gitea is local code authority; GitHub is backup/upstream. Never assert a commit to Gitea without evidence from the local forge.
6. Do not confuse model statements with execution evidence. No auto-merges into protected branches. STOP must work independently of Qwen, including while phone/UI is disconnected.
7. No unbounded paid API calls, retries or background agent work. Use hard budgets, task-scoped authorizations and immutable revision bindings.
8. All significant new development files and staging on E:, retaining existing small runtime state where already proven.

## Components and responsibilities
- ORION controller: task ledger, immutable event IDs, approvals, policy, execution leases, budgets, STOP, evidence authentication, recovery.
- Qwen 9B: retrieve project memory, decompose approved goal, route requests, follow task status, submit Gitea/Hands actions via ORION; no code authoring.
- DeepSeek Flash (API key not yet provisioned): architecture, code patches, final technical resolution after review.
- Free cloud reviewer: adversarial independent review through existing provider gateway, with provider fallback and quota tracking.
- Alook: donor for agent identity, message envelope, rooms/threads, delivery/reconnect concepts. Reuse isolated code if compatible; DO NOT deploy its entire Cloudflare/Next/Bun stack.
- Claude HTML writing interface: presentation and owner controls for messages, code diffs, Gitea events, Hands logs, task history. Backend remains ORION.
- MyGitea2: isolated task branches, commits, tested revision identities.
- ORION internal Hands: authorized file/test operations and real logs, not TheHands-.
- Laya: optional donor for lightweight actions only after audit proves it adds value without duplicating internal Hands.
- Android ORION: owner approval inbox, actionable notification, task status, budget visibility and reliable STOP. Approvals bind to exact operation, scope and revision.

## Data and event contract — candidate to verify against existing code
Each task has task_id, project_id, goal, allowed_repo, branch, base_revision, context_snapshot_id, authorization_id, budget, status.
Each AI message has message_id, task_id, thread_id, sender_role, recipient_role, timestamp, model/provider, body/artifact references and provenance.
Each proposal has proposal_id, task_id, base_revision, patch hash, affected paths, reviewer verdict, DeepSeek final decision.
Each execution has lease_id, task_id, revision, bounded command, executor identity, exit code, log/evidence hash, verifier verdict.
Each owner decision has approval_id, exact proposed operation and revision, expiry, decision, and audit event.
Reuse existing schema where possible; do not create another DB or a competing canonical state.

## Loop
Owner goal -> Qwen retrieves scoped memory + actual repository state -> DeepSeek creates code proposal -> free cloud model reviews -> DeepSeek decides -> ORION deterministic policy gate -> authorized task branch write to Gitea -> ORION internal Hands test exact revision -> authenticated PASS/FAIL -> failures returned to DeepSeek within bounded retries -> verified result documented and frozen. All events appear in writing UI and Android; closing UI does not interrupt authorized PC work.

## Approval-by-exception
GREEN: preauthorized isolated work, routine review, bounded testing and repairs.
YELLOW: frozen-interface changes, migrations, expanded scope or high-risk actions: pause only affected task, notify owner Android.
RED: unauthorized destructive actions, exceeded budgets, invalid scope, unsafe STOP: reject/stop.
Qwen requests approvals, but cannot grant itself authorization. Owner may approve once, reject, inspect evidence or STOP.

## Roadmap and step ledger (mark only after proof)
| Step | Deliverable | Acceptance | Status |
| --- | --- | --- | --- |
| 0 | Preserve agreed architecture and boundaries | New isolated document in branch; no frozen source edits | IN PROGRESS |
| 1 | Read-only repo audit of ORION, UI, Hands, memory, cloud adapters, Alook, Laya | Exact paths/functions, reuse matrix, missing seams and baseline GITCHECK | NOT STARTED |
| 2 | ORION agent communication module | Qwen/DeepSeek/reviewer messages persisted and replayable after restart | NOT STARTED |
| 3 | Qwen coordinator and scoped context compiler | Correct project context and durable task routing without Qwen coding | NOT STARTED |
| 4 | DeepSeek Flash + free reviewer | Real API calls, independent review, structured final technical decision, budget gates | BLOCKED: DeepSeek API credentials pending |
| 5 | Gitea + ORION internal Hands closed loop | Task branch, exact tested revision, real FAIL -> repair -> authenticated PASS | NOT STARTED |
| 6 | Claude HTML writing interface integration | Live and historical AI chat, diffs, commits, logs from ORION events | NOT STARTED |
| 7 | Android approvals and notifications | Remote approval/rejection, auditable revision-bound action, reliable STOP | NOT STARTED |
| 8 | Unattended recovery and freeze | Resume after restart, no duplicate execution, budgets and STOP verified | NOT STARTED |

## Test discipline
- Before any source change: inspect frozen inventory and baseline; use isolated new modules and candidate branches.
- Bundle related small tests into one GITCHECK run through TheHands- remote.
- Record each PASS/FAIL with revision, actual test count, log, observed behavior and freeze decision.
- Failed step remains FAIL, never quietly marked PASS. Revisions after PASS require new module or explicit owner exception.
- Manual testing is permitted but must be identified as manual. No fabricated tests, source-level PASS masquerading as deployed PASS, or claim that local Gitea was changed by a GitHub-only operation.

## Immediate next action
Step 1: read-only inspect existing ORION modules and HTML UI, identify exact reusable Alook messaging source and Laya scope. Do not code the loop before completing the audit and choosing smallest integration seams.
