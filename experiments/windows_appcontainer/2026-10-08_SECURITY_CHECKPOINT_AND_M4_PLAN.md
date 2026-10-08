# ORION V3 — Windows isolation checkpoint and Milestone 4 handoff
Date: 2026-10-08
Status: experimental branch; real ORION execution remains DISABLED until a bounded task's preflight explicitly qualifies it.
Decision: stop expanding WFP audit research; reuse existing safety controls; prioritize first bounded, disposable ORION→Hands execution.

## Architecture and boundaries
- Owner approves; ORION owns policy, scope, STOP, evidence and Vault commit authority; Hands executes bounded instructions. Models do not grant themselves permissions.
- Remote V1 and frozen TheHands product remain unchanged. All new tests use disposable fixtures and experimental ORION files.
- Keep all components replaceable. No silent promotion of inconclusive evidence to PASS.

## Physical results
- Cross-process STOP + real Vault: TheHands session 03bb1e6561a0; 9/9 reported PASS. Commit/crash linearization is explicitly NOT QUALIFIED.
- Windows AppContainer filesystem: session af7a5f6970d7; native child launched; workspace read/write ALLOW; outside read/write DENY; outside fixture unchanged; disposable profile deleted. PASS for disposable fixture only.
- Network: same session; host listener control PASS, native child WSAStartup=0, nonblocking connection to loopback timed out (child exit 12). No connection observed in that probe. Verdict INCONCLUSIVE as a universal network-isolation claim; no WSAEACCES or correlated WFP event. This must not be reclassified as verified kernel denial.
- WFP event read-only diagnostic: session fe4793d2cc05 PASS for script completion; no 5152/5157 events found; network still INCONCLUSIVE.
- WFP audit readiness: session c3153579e93c PASS for script completion; auditpol /get both subcategories returned 1314 required privilege not held; Security log read unauthorized; no events. No audit or firewall settings changed. Network still INCONCLUSIVE.
- GitHub commits: WFP diagnostic ORION 3217594; TheHands staging cac12c9; checkpoint 2f64266; readiness probe ORION 171a7d6; TheHands staging 1917db9.
- Some later GitHub write attempts were blocked by safety checks; do not assume those files/updates exist.

## Donor review
- Forks verified: Sadusor/OpenSandbox, OpenHands, cua, OpenJarvis, mantis.
- OpenSandbox offers sandbox lifecycle and fail-closed policy patterns; its egress implementation uses Linux namespaces/nftables and is not drop-in native Windows code. Do not replace already-working Windows substrate before benchmarking.
- OpenHands and cua are secondary execution/desktop donors; OpenJarvis is a low-consumption runtime/measurement donor; mantis is a security-review donor.
- Review was documentation-level, not a line-by-line code reuse audit.

## Explicit decision and limitations
- Single-user personal assistant threat model; avoid disproportionate security research. DeepSeek advised accepting timeout operationally and shipping the product.
- Adopt the prioritization, NOT the claim that a timeout proves all network paths are denied.
- No further WFP audit escalation or administrator privilege changes in this phase. First bounded task must require no network and cannot rely on universal network denial as a proven security boundary.
- Preserve strict STOP, scope restrictions, timeouts, disposable workspace, evidence and no automatic retries after crash.
- Do not mark full descendant STOP, crash/commit safety, or combined 8-gate sandbox qualification PASS without evidence.

## Milestone 4: first bounded real execution
1. Inspect current ORION work-loop, approval, scope and Hands adapter contracts before touching code.
2. Prepare an isolated disposable workspace, predeclared harmless action (create one text file), explicit approval, tight timeout, and a dedicated killable child process; deny unapproved paths.
3. Stage a single GitCheck with machine-readable evidence for: approval, workspace scope, task execution, file content verification, STOP availability, cleanup and fail-closed error behavior.
4. Do not change Remote V1 or frozen TheHands modules. Keep real execution disabled outside this one bounded fixture.
5. After physical PASS, document result and proceed to PC/Android UI integration, Qwen/cloud orchestration and latency/power benchmarks.

## Definition of done for this checkpoint
Decision recorded; previous PASS/FAIL/INCONCLUSIVE evidence preserved; next work is bounded product execution rather than further WFP diagnostics.

## Roadmap reconciliation — important correction
The canonical `docs/ROADMAP.md` defines Milestone 4 as an all-or-nothing **FAIL-across-restart autonomous loop** with 15 acceptance conditions, not merely creation of a text file. The small file task is a **preliminary execution smoke test**, not Milestone 4 PASS. It must not silently replace the existing milestone. The roadmap also names a preceding read-observation non-promotion and Vault seam check. Before staging real execution, inspect actual work_loop modules and preserve existing ORION approval/STOP authority. This checkpoint's earlier wording was too broad; this paragraph corrects it.

## DeepSeek adversarial review — staged execution decision
Source: owner-provided review 2026-10-08. Adopt a Milestone 3.5 pipeline smoke gate before full Milestone 4, without weakening Milestone 4's canonical 15 acceptance conditions. Sequence: (1) audit actual existing STOP/Vault/verifier/AppContainer/Hand entrypoints and signatures; (2) manual approved append-one-line in disposable E: workspace, independent verify and exactly-once Vault commit with STOP handling; (3) Qwen proposal adapter only, no authority; (4) restart/interruption recovery without auto-retry; (5) verified FAIL→repair→PASS continuity. Stage separately and record physical evidence per step. TheHands remains frozen engineering transport, NOT ORION's internal Hand adapter. No second STOP/Vault/verifier/Hand architecture. Network probe timeout remains inconclusive as a universal isolation guarantee. Atomic commit may finish if it linearized before STOP; do not claim that STOP can retroactively abort it. Avoid UI polish, WFP investigation, multi-agent councils and extra framework work until the bounded pipeline works. Do not delete historical fixtures or evidence. Milestone 3.5 is a preliminary gate, not Milestone 4 PASS.
