# ORION V3 Gitea and Qwen — checkpoint (2026-10-10)

## Locked direction
Qwen 9B coordinates authorized repository discovery, project context, code-generation delegation and progress through the existing ORION PC/phone UI. DeepSeek Flash is the initial proposed code generator. ORION retains approval, STOP, verification, memory promotion and canonical state authority. ORION's own internal Work Hands eventually execute approved changes and Git pushes to MyGitea2. Codespace is a display-only view. TheHands is a separate remote product used only for PowerShell 1 qualification tests. Existing frozen modules remain untouched.

## Verified
- MyGitea2 API on local port 3001, Gitea 1.27.1: session b7dfc1c51f09 PASS.
- Gitea adapter and mapper tests: session 0f893ac001af PASS 8/8.
- First 50 visible repositories: session 3df5af96c917 PASS.
- MyGitea/ORION-V3 actual Git tree at be618edb8cd40a7e5da0210ef1b4599a0cfbf220: session 0d7a4ee27a62 PASS, 269 mapped code/document files.
- Gitea connector, map and source-context isolated tests: 13/13 PASS in session 3d6847baa764. That overall session FAILED at live source reading: HTTP 404 for a GitHub-side path assumed to exist in local Gitea.
- Latest session 22f63a44a725 FAILED before testing, because E:\ORION-WORK\gitea-source-batch-20261010-01 already existed. It does not establish any source-reader failure.

## New files
src/orion_v3/modules/gitea_readonly_v1.py; gitea_codebase_map_v1.py; gitea_source_context_v1.py; related tests under tests/test_gitea*_v1.py. Owner-approved architecture in docs/ORION_CODESPACE_QWEN_GITEA_ROADMAP_2026-10-10.md.

## Not yet proven
Live Gitea file-content retrieval, authenticated private repo discovery, complete paginated inventory, Qwen live source tools, paid DeepSeek adapter, authorized internal Hands Git pushes, integrated Codespace display.

## Resume safely
1. Preserve old test checkout; use a unique fresh folder; run the 13 contract tests and inspect actual local tree for a valid source file.
2. Verify Gitea contents API against that exact file and commit; do not assume local Gitea matches GitHub.
3. Use commit-pinned project-scoped code retrieval as untrusted context to Qwen; no automatic canonical-memory promotion.
4. Qualify Windows isolation, independent evidence and STOP before any automated file writes/pushes.
5. Do not edit Gitea SQLite or repository backing directories; use supported REST and Git interfaces.

## Update — live source content PASS
TheHands PowerShell 1 session `85ba347178fa`, task source commit `9d2f694321304ff549a125bac58793e318e859ae`: overall PASS. All 13 read-only Gitea module tests PASS. Real Gitea `MyGitea/ORION-V3` at commit `be618edb8cd40a7e5da0210ef1b4599a0cfbf220`: 53 Python candidates; successfully retrieved `android/scripts/check_screen.py` (1368 characters), tagged `untrusted_source`. The earlier HTTP 404 was due to assuming the local import contained a newer GitHub path; the second failure was a reused checkout directory. Both diagnostic blockers are resolved. Freeze this proven read-only source access interface as baseline. Next: new project-scoped source-context orchestration module and tests; wiring into Qwen UI is not yet proven. No Gitea writes or direct database access were performed.
