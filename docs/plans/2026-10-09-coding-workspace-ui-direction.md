# ORION V3 — Coding workspace UI direction (deferred decision)

Status: DESIGN INTENT ONLY — revisit after the resilient multi-AI coding council passes live end-to-end tests.

## Product direction
Do not make the Jarvis-like visual shell the entire interface. Build a replaceable AI development workspace inspired by the useful interaction patterns of Codex, Claude Code and Cursor, while retaining ORION's visual identity.

## Workspace requirements
- Project/task navigator, Git branches and checkpoints, chat/session history, searchable logs.
- Council view: independent author and reviewer slots, model family, selected provider, quota/rate-limit cooldown and failover evidence. Never expose API credentials.
- Plan approval: owner-visible proposal, critiques, exact digest and explicit approve/reject before any execution.
- Work view: code diffs, file tree, tests, failures, artifacts, evidence, STOP and current task state.
- Phone: lightweight task overview, approval, STOP, evidence, and optional desktop viewing. PC: full code/diff workspace.
- Backend authoritative status with live updates and STALE indication, never fabricated UI success.
- Keep the existing frozen V1 Remote untouched. TheHands is a separate project and only a temporary physical test launcher, not an ORION module.
- Preserve ORION's memory visualization as an optional panel rather than the main coding cockpit.
- Separate UI adapters from council routing, memory, native Work Hand, and authority/policy.
- No UI implementation until the free-provider router and council prove real resilient end-to-end coding work.

## Next design review
After live loop proof, compare actual Codex/Claude Code/Cursor workflows and make PC/phone wireframes based on observed ORION events, not mock capabilities. Do not conflate planning, proposal, approval and execution.
